from django.urls import reverse_lazy
from django.http import HttpResponse, HttpRequest

from django.contrib.auth import authenticate, login, logout
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, reverse, get_object_or_404, redirect
from django.views.generic import TemplateView, CreateView, DeleteView, View
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LogoutView
from .models import Profile


from .models import Product, Cart

def shop_index(request: HttpRequest) -> HttpResponse:
    products = Product.objects.order_by('-id')[:3]
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1
    return render(request, 'shopapp/shop-index.html', context={'num_visits': num_visits, 'products': products})


class ProductsListView(ListView):
    template_name = "shopapp/products-list.html"
    context_object_name = "products"
    queryset = Product.objects.all()

class ProductDetailsView(DetailView):
    template_name = 'shopapp/products-details.html'
    model = Product
    context_object_name = "product"

    def get_object(self):
        obj = super().get_object()
        obj.views_count += 1
        obj.save()
        return obj

class ProductCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "shopapp.add_product"

    model = Product
    fields = "name", "price", "description", "discount", "preview"
    success_url = reverse_lazy("shopapp:products-list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        return response

class ProductUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "shopapp.change_product"

    model = Product
    fields = "name", "price", "description", "discount", "preview"
    template_name_suffix = "_update_form"

    def get_success_url(self):
        return reverse(
            "shopapp:product_details",
            kwargs={"pk": self.object.pk}
        )



class ProductDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = "shopapp.delete_product"

    model = Product
    template_name = 'shopapp/products-delete.html'

    def get_success_url(self):
        return reverse(
            "shopapp:products-list",
        )



class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = "myauth/register.html"
    success_url = reverse_lazy("myauth:about-me")

    def form_valid(self, form):
        response = super().form_valid(form)
        Profile.objects.create(user=self.object)
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password1")

        user = authenticate(
            self.request,
            username=username,
            password=password,
        )
        login(request=self.request, user=user)
        return response


class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = "shopapp/register.html"
    success_url = reverse_lazy("shopapp:about-me")

    def form_valid(self, form):
        response = super().form_valid(form)
        Profile.objects.create(user=self.object)
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password1")

        user = authenticate(
            self.request,
            username=username,
            password=password,
        )
        login(request=self.request, user=user)
        return response


class AboutMeView(TemplateView):
    template_name = "shopapp/about-me.html"

class AboutMeUpdateView(UserPassesTestMixin, UpdateView):
    def test_func(self):
        if self.request.user.is_staff:
            return True
        return True
    model = Profile
    fields = "user", 'last_name', 'first_name', 'email',
    template_name_suffix = "_update_form"

    def get_success_url(self):
        return reverse(
            "shopapp:about-me",
        )

class MyLogoutView(LogoutView):
    next_page = reverse_lazy("shopapp:login")


class Search(ListView):
    template_name = "shopapp/products-list.html"
    context_object_name = "products"
    paginate_by = 5

    def get_queryset(self):
        return Product.objects.filter(name__iregex=self.request.GET.get('q'))

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q')
        return context

def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    context = {'cart_items': cart_items}
    return render(request, 'shopapp/cart.html', context)

def add_to_cart(request, pk):
    product = Product.objects.get(pk=pk)
    cart_item = Cart.objects.filter(product=product, user=request.user).first()
    if cart_item:
        cart_item.quantity += 1
        cart_item.save()
    else:
        cart_item = Cart(user=request.user, product=product)
        cart_item.save()
    return redirect('shopapp:view_cart')

def remove_from_cart(request, pk):
    cart_item = Cart.objects.get(pk=pk, user=request.user)
    cart_item.delete()
    return redirect('shopapp:view_cart')

