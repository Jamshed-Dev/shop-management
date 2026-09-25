from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import reverse
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal

from .models import (
    Collection, ProductType, ProductChoice, ProductChoiceValue,
    Product, ProductImage, ProductVariant,
    Order, OrderItem, OrderStatusLog, InventoryTransaction
)
from .services import InventoryService, StatusService, OrderService

# Site Header & Titles Branding
admin.site.site_header = "Shop Management Administration"
admin.site.site_title = "Shop Management Admin"
admin.site.index_title = "Shop Management Control Panel"


# -------------------------------------------------------------
# Collections Admin
# -------------------------------------------------------------
@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('image_preview', 'title', 'slug', 'products_count', 'is_active', 'created_at')
    search_fields = ('title', 'slug', 'description')
    list_filter = ('is_active', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    actions = ['make_active', 'make_inactive']

    def image_preview(self, obj):
        img_src = obj.image.url if obj.image else obj.image_url
        if img_src:
            return format_html(
                '<img src="{}" style="width: 42px; height: 42px; object-fit: cover; border-radius: 6px; border: 1px solid #dee2e6;" />',
                img_src
            )
        return format_html('<span style="color: #adb5bd; font-size: 11px;">No image</span>')
    image_preview.short_description = "Image"

    def products_count(self, obj):
        count = obj.products.count()
        url = reverse('admin:store_product_changelist') + f'?collection__id__exact={obj.id}'
        return format_html('<a href="{}" style="font-weight: 600;">{} products</a>', url, count)
    products_count.short_description = "Products"

    @admin.action(description="Mark selected collections as Active")
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} collection(s) marked as active.")

    @admin.action(description="Mark selected collections as Inactive")
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} collection(s) marked as inactive.")


# -------------------------------------------------------------
# Product Types Admin
# -------------------------------------------------------------
@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'products_count', 'is_active', 'created_at')
    search_fields = ('title', 'slug', 'description')
    list_filter = ('is_active', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    actions = ['make_active', 'make_inactive']

    def products_count(self, obj):
        count = obj.products.count()
        url = reverse('admin:store_product_changelist') + f'?product_type__id__exact={obj.id}'
        return format_html('<a href="{}" style="font-weight: 600;">{} products</a>', url, count)
    products_count.short_description = "Products"

    @admin.action(description="Mark selected product types as Active")
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} product type(s) marked as active.")

    @admin.action(description="Mark selected product types as Inactive")
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} product type(s) marked as inactive.")


# -------------------------------------------------------------
# Product Choices & Values Admin
# -------------------------------------------------------------
class ProductChoiceValueInline(admin.TabularInline):
    model = ProductChoiceValue
    extra = 2
    fields = ('value', 'slug')
    prepopulated_fields = {'slug': ('value',)}


@admin.register(ProductChoice)
class ProductChoiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'values_display', 'is_active', 'created_at')
    search_fields = ('title', 'slug', 'description')
    list_filter = ('is_active',)
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProductChoiceValueInline]

    def values_display(self, obj):
        vals = [v.value for v in obj.values.all()[:8]]
        if not vals:
            return format_html('<span style="color: #adb5bd;">None</span>')
        badges = "".join([f'<span style="background: #e9ecef; color: #495057; padding: 2px 7px; border-radius: 4px; margin-right: 4px; font-size: 11px;">{v}</span>' for v in vals])
        if obj.values.count() > 8:
            badges += f'<span style="color: #6c757d; font-size: 11px;">+{obj.values.count() - 8} more</span>'
        return format_html(badges)
    values_display.short_description = "Values"


@admin.register(ProductChoiceValue)
class ProductChoiceValueAdmin(admin.ModelAdmin):
    list_display = ('value', 'choice', 'slug', 'created_at')
    search_fields = ('value', 'choice__title', 'slug')
    list_filter = ('choice', 'created_at')


# -------------------------------------------------------------
# Product Images & Variants Inlines
# -------------------------------------------------------------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('thumbnail', 'image', 'image_url', 'alt_text', 'sort_order', 'is_primary')
    readonly_fields = ('thumbnail',)

    def thumbnail(self, obj):
        img_src = obj.image.url if obj.image else obj.image_url
        if img_src:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px;" />',
                img_src
            )
        return format_html('<span style="color: #adb5bd; font-size: 11px;">No image</span>')
    thumbnail.short_description = "Preview"


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ('sku', 'choices', 'price_override', 'stock', 'is_active')
    filter_horizontal = ('choices',)


# -------------------------------------------------------------
# Product Variant Standalone Admin
# -------------------------------------------------------------
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('sku', 'product_link', 'choices_display', 'price_override', 'effective_price_display', 'stock', 'stock_badge', 'is_active')
    list_editable = ('stock', 'price_override', 'is_active')
    search_fields = ('sku', 'product__title', 'product__sku')
    list_filter = ('is_active', 'product__collection', 'product__product_type')
    filter_horizontal = ('choices',)

    def product_link(self, obj):
        url = reverse('admin:store_product_change', args=[obj.product.id])
        return format_html('<a href="{}" style="font-weight: 600;">{}</a>', url, obj.product.title)
    product_link.short_description = "Product"

    def choices_display(self, obj):
        vals = [str(c) for c in obj.choices.all()]
        if not vals:
            return "-"
        return format_html(", ".join(vals))
    choices_display.short_description = "Selected Choices"

    def effective_price_display(self, obj):
        if obj.price_override is not None:
            return f"${obj.price_override}"
        return f"${obj.product.current_price} (Product)"
    effective_price_display.short_description = "Active Price"

    def stock_badge(self, obj):
        if obj.stock <= 0:
            return format_html('<span style="background: #f8d7da; color: #842029; padding: 2px 7px; border-radius: 4px; font-weight: 600; font-size: 11px;">Out of Stock</span>')
        elif obj.stock <= 5:
            return format_html('<span style="background: #fff3cd; color: #664d03; padding: 2px 7px; border-radius: 4px; font-weight: 600; font-size: 11px;">Low ({})</span>', obj.stock)
        return format_html('<span style="background: #d1e7dd; color: #0f5132; padding: 2px 7px; border-radius: 4px; font-weight: 600; font-size: 11px;">In Stock ({})</span>', obj.stock)
    stock_badge.short_description = "Status"

    def save_model(self, request, obj, form, change):
        if change and 'stock' in form.changed_data:
            orig = ProductVariant.objects.get(pk=obj.pk)
            old_stock = orig.stock
            new_stock = obj.stock
            super().save_model(request, obj, form, change)
            if old_stock != new_stock:
                InventoryTransaction.objects.create(
                    product=obj.product,
                    variant=obj,
                    transaction_type='adjustment',
                    quantity=new_stock - old_stock,
                    stock_before=old_stock,
                    stock_after=new_stock,
                    reason=f"Stock updated to {new_stock} via Variant Admin",
                    created_by=request.user if request.user.is_authenticated else None
                )
        else:
            super().save_model(request, obj, form, change)


# -------------------------------------------------------------
# Products Admin
# -------------------------------------------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'image_thumbnail', 'title', 'sku', 'collection', 'product_type',
        'price_display', 'stock', 'stock_badge', 'variants_count',
        'is_active', 'is_featured'
    )
    list_editable = ('stock', 'is_active', 'is_featured')
    search_fields = ('title', 'sku', 'description', 'short_description')
    list_filter = ('is_active', 'is_featured', 'collection', 'product_type', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('image_preview_large', 'current_price_display', 'created_at', 'updated_at')
    inlines = [ProductImageInline, ProductVariantInline]
    actions = ['make_active', 'make_inactive', 'make_featured', 'remove_featured']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'sku', 'collection', 'product_type')
        }),
        ('Pricing', {
            'fields': ('main_price', 'new_price', 'old_price', 'current_price_display')
        }),
        ('Inventory', {
            'fields': ('stock', 'low_stock_threshold')
        }),
        ('Media & Display', {
            'fields': ('image', 'image_url', 'image_preview_large')
        }),
        ('Descriptions', {
            'classes': ('collapse',),
            'fields': ('short_description', 'description')
        }),
        ('Visibility & Audit', {
            'fields': ('is_active', 'is_featured', 'created_at', 'updated_at')
        }),
    )

    def image_thumbnail(self, obj):
        img_src = obj.image.url if obj.image else obj.image_url
        if img_src:
            return format_html(
                '<img src="{}" style="width: 42px; height: 42px; object-fit: cover; border-radius: 6px; border: 1px solid #dee2e6;" />',
                img_src
            )
        return format_html('<span style="color: #adb5bd; font-size: 11px;">No image</span>')
    image_thumbnail.short_description = "Image"

    def image_preview_large(self, obj):
        img_src = obj.image.url if obj.image else obj.image_url
        if img_src:
            return format_html(
                '<img src="{}" style="max-width: 250px; max-height: 250px; object-fit: contain; border-radius: 8px; border: 1px solid #ced4da;" />',
                img_src
            )
        return "No image uploaded."
    image_preview_large.short_description = "Current Image Preview"

    def price_display(self, obj):
        if obj.new_price:
            return format_html(
                '<span style="color: #198754; font-weight: 600;">${}</span> <del style="color: #6c757d; font-size: 11px;">${}</del>',
                obj.new_price, obj.main_price
            )
        return format_html('<span>${}</span>', obj.main_price)
    price_display.short_description = "Price"

    def current_price_display(self, obj):
        return f"${obj.current_price}"
    current_price_display.short_description = "Effective Selling Price"

    def stock_badge(self, obj):
        if obj.stock <= 0:
            return format_html('<span style="background: #f8d7da; color: #842029; padding: 2px 7px; border-radius: 4px; font-weight: 600; font-size: 11px;">Out of Stock</span>')
        elif obj.stock <= obj.low_stock_threshold:
            return format_html('<span style="background: #fff3cd; color: #664d03; padding: 2px 7px; border-radius: 4px; font-weight: 600; font-size: 11px;">Low Stock</span>')
        return format_html('<span style="background: #d1e7dd; color: #0f5132; padding: 2px 7px; border-radius: 4px; font-weight: 600; font-size: 11px;">In Stock</span>')
    stock_badge.short_description = "Stock Status"

    def variants_count(self, obj):
        count = obj.variants.count()
        if count > 0:
            url = reverse('admin:store_productvariant_changelist') + f'?product__id__exact={obj.id}'
            return format_html('<a href="{}" style="font-weight: 600;">{} variants</a>', url, count)
        return "0"
    variants_count.short_description = "Variants"

    def save_model(self, request, obj, form, change):
        if change and 'stock' in form.changed_data:
            orig = Product.objects.get(pk=obj.pk)
            old_stock = orig.stock
            new_stock = obj.stock
            super().save_model(request, obj, form, change)
            if old_stock != new_stock:
                InventoryTransaction.objects.create(
                    product=obj,
                    transaction_type='adjustment',
                    quantity=new_stock - old_stock,
                    stock_before=old_stock,
                    stock_after=new_stock,
                    reason=f"Stock updated to {new_stock} via Product Admin",
                    created_by=request.user if request.user.is_authenticated else None
                )
        else:
            super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        if formset.model == ProductVariant:
            instances = formset.save(commit=False)
            for instance in instances:
                if instance.pk:
                    orig = ProductVariant.objects.get(pk=instance.pk)
                    old_stock = orig.stock
                    instance.save()
                    if old_stock != instance.stock:
                        InventoryTransaction.objects.create(
                            product=instance.product,
                            variant=instance,
                            transaction_type='adjustment',
                            quantity=instance.stock - old_stock,
                            stock_before=old_stock,
                            stock_after=instance.stock,
                            reason=f"Stock updated to {instance.stock} via Product Page Variant Inline",
                            created_by=request.user if request.user.is_authenticated else None
                        )
                else:
                    instance.save()
                    if instance.stock > 0:
                        InventoryTransaction.objects.create(
                            product=instance.product,
                            variant=instance,
                            transaction_type='manual_add',
                            quantity=instance.stock,
                            stock_before=0,
                            stock_after=instance.stock,
                            reason="Initial stock for new variant",
                            created_by=request.user if request.user.is_authenticated else None
                        )
            formset.save_m2m()
        else:
            super().save_formset(request, form, formset, change)

    @admin.action(description="Mark selected products as Active")
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} product(s) marked as active.")

    @admin.action(description="Mark selected products as Inactive")
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} product(s) marked as inactive.")

    @admin.action(description="Mark selected products as Featured")
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"{updated} product(s) marked as featured.")

    @admin.action(description="Remove selected products from Featured")
    def remove_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f"{updated} product(s) removed from featured.")


# -------------------------------------------------------------
# Orders Admin & Inlines
# -------------------------------------------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'variant', 'unit_price', 'quantity', 'subtotal', 'returned_quantity')
    readonly_fields = ('subtotal',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class OrderStatusLogInline(admin.TabularInline):
    model = OrderStatusLog
    extra = 0
    fields = ('old_status', 'new_status', 'changed_by', 'note', 'created_at')
    readonly_fields = ('old_status', 'new_status', 'changed_by', 'note', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'customer_info', 'status_badge', 'payment_badge',
        'payment_method_display', 'items_count', 'subtotal_display',
        'discount_display', 'shipping_display', 'total_display', 'created_at'
    )
    search_fields = ('order_number', 'customer_name', 'customer_phone', 'customer_email', 'shipping_address')
    list_filter = ('status', 'payment_status', 'payment_method', 'created_at')
    readonly_fields = ('order_number', 'subtotal', 'total', 'created_at', 'updated_at')
    inlines = [OrderItemInline, OrderStatusLogInline]

    actions = [
        'dispatch_selected_orders',
        'mark_as_confirmed',
        'mark_as_processing',
        'mark_as_delivered',
        'cancel_selected_orders',
        'process_full_return',
        'mark_payment_paid',
        'mark_payment_refunded',
    ]

    fieldsets = (
        ('Order & Status', {
            'fields': ('order_number', 'user', 'status', 'payment_status', 'payment_method')
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'customer_phone', 'customer_email')
        }),
        ('Delivery & Notes', {
            'fields': ('shipping_address', 'billing_address', 'notes')
        }),
        ('Financial Summary', {
            'fields': ('subtotal', 'discount', 'shipping_cost', 'tax', 'total')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def customer_info(self, obj):
        return format_html(
            '<div><strong>{}</strong><br/><span style="color: #6c757d; font-size: 11px;">{}</span></div>',
            obj.customer_name, obj.customer_phone
        )
    customer_info.short_description = "Customer"

    def status_badge(self, obj):
        status_colors = {
            'pending': '#ffc107',        # warning yellow
            'confirmed': '#0dcaf0',      # info cyan
            'processing': '#0d6efd',     # primary blue
            'dispatched': '#6f42c1',     # purple
            'delivered': '#198754',      # success green
            'cancelled': '#dc3545',      # danger red
            'return_requested': '#fd7e14', # orange
            'returned': '#6c757d',       # secondary grey
            'partially_returned': '#20c997', # teal
        }
        color = status_colors.get(obj.status, '#6c757d')
        text_color = '#000' if obj.status in ['pending', 'confirmed'] else '#fff'
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 11px; text-transform: uppercase;">{}</span>',
            color, text_color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def payment_badge(self, obj):
        payment_colors = {
            'paid': ('#d1e7dd', '#0f5132'),
            'pending': ('#fff3cd', '#664d03'),
            'failed': ('#f8d7da', '#842029'),
            'refunded': ('#cfe2ff', '#084298'),
        }
        bg, text = payment_colors.get(obj.payment_status, ('#e2e3e5', '#383d41'))
        return format_html(
            '<span style="background: {}; color: {}; padding: 2px 7px; border-radius: 4px; font-weight: 600; font-size: 11px; text-transform: uppercase;">{}</span>',
            bg, text, obj.get_payment_status_display()
        )
    payment_badge.short_description = "Payment"

    def payment_method_display(self, obj):
        return obj.payment_method or "N/A"
    payment_method_display.short_description = "Method"

    def items_count(self, obj):
        return f"{obj.items.count()} items"
    items_count.short_description = "Items"

    def subtotal_display(self, obj):
        return f"${obj.subtotal}"
    subtotal_display.short_description = "Subtotal"

    def discount_display(self, obj):
        if obj.discount > 0:
            return format_html('<span style="color: #dc3545;">-${}</span>', obj.discount)
        return "$0.00"
    discount_display.short_description = "Discount"

    def shipping_display(self, obj):
        return f"${obj.shipping_cost}"
    shipping_display.short_description = "Shipping"

    def total_display(self, obj):
        return format_html('<strong style="font-size: 13px;">${}</strong>', obj.total)
    total_display.short_description = "Total"

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            orig = Order.objects.get(pk=obj.pk)
            old_status = orig.status
            new_status = obj.status

            if new_status == 'dispatched' and old_status != 'dispatched':
                try:
                    # Invoke InventoryService strictly to deduct stock & record inventory transactions
                    InventoryService.dispatch_order(orig, request.user)
                    obj.refresh_from_db()
                    self.message_user(request, f"Order {obj.order_number} dispatched and inventory deducted successfully.", level=messages.SUCCESS)
                    return
                except ValidationError as e:
                    self.message_user(request, f"Dispatch failed: {e}", level=messages.ERROR)
                    obj.status = old_status
                    super().save_model(request, obj, form, change)
                    return
            elif new_status != old_status:
                try:
                    StatusService.change_status(
                        orig, new_status, request.user,
                        note="Status changed via Django Administration"
                    )
                    obj.refresh_from_db()
                    self.message_user(request, f"Order status changed to {new_status}.", level=messages.SUCCESS)
                    return
                except ValidationError as e:
                    self.message_user(request, f"Status change failed: {e}", level=messages.ERROR)
                    obj.status = old_status

        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # Recalculate totals from items
        order = form.instance
        subtotal = sum(item.subtotal for item in order.items.all())
        order.subtotal = subtotal
        order.total = max(Decimal('0.00'), subtotal + order.shipping_cost + order.tax - order.discount)
        order.save(update_fields=['subtotal', 'total'])

    # ---------------- ADMIN ACTIONS ----------------
    @admin.action(description="🚀 Dispatch selected orders (Deduct stock & log)")
    def dispatch_selected_orders(self, request, queryset):
        success_count = 0
        error_count = 0
        for order in queryset:
            try:
                InventoryService.dispatch_order(order, request.user)
                success_count += 1
            except ValidationError as e:
                error_count += 1
                self.message_user(request, f"Order {order.order_number}: {e}", level=messages.ERROR)

        if success_count > 0:
            self.message_user(request, f"Successfully dispatched {success_count} order(s).", level=messages.SUCCESS)

    @admin.action(description="✓ Mark selected orders as Confirmed")
    def mark_as_confirmed(self, request, queryset):
        count = 0
        for order in queryset:
            try:
                StatusService.change_status(order, 'confirmed', request.user, note="Confirmed via Django Admin action")
                count += 1
            except ValidationError as e:
                self.message_user(request, f"Order {order.order_number}: {e}", level=messages.WARNING)
        if count > 0:
            self.message_user(request, f"{count} order(s) marked as Confirmed.", level=messages.SUCCESS)

    @admin.action(description="⚙ Mark selected orders as Processing")
    def mark_as_processing(self, request, queryset):
        count = 0
        for order in queryset:
            try:
                StatusService.change_status(order, 'processing', request.user, note="Processing via Django Admin action")
                count += 1
            except ValidationError as e:
                self.message_user(request, f"Order {order.order_number}: {e}", level=messages.WARNING)
        if count > 0:
            self.message_user(request, f"{count} order(s) marked as Processing.", level=messages.SUCCESS)

    @admin.action(description="🚚 Mark selected orders as Delivered")
    def mark_as_delivered(self, request, queryset):
        count = 0
        for order in queryset:
            try:
                StatusService.change_status(order, 'delivered', request.user, note="Delivered via Django Admin action")
                count += 1
            except ValidationError as e:
                self.message_user(request, f"Order {order.order_number}: {e}", level=messages.WARNING)
        if count > 0:
            self.message_user(request, f"{count} order(s) marked as Delivered.", level=messages.SUCCESS)

    @admin.action(description="✕ Cancel selected orders")
    def cancel_selected_orders(self, request, queryset):
        count = 0
        for order in queryset:
            try:
                StatusService.change_status(order, 'cancelled', request.user, note="Cancelled via Django Admin action")
                count += 1
            except ValidationError as e:
                self.message_user(request, f"Order {order.order_number}: {e}", level=messages.WARNING)
        if count > 0:
            self.message_user(request, f"{count} order(s) cancelled.", level=messages.SUCCESS)

    @admin.action(description="💳 Mark payment as Paid")
    def mark_payment_paid(self, request, queryset):
        updated = queryset.update(payment_status='paid')
        self.message_user(request, f"{updated} order(s) marked as Paid.", level=messages.SUCCESS)

    @admin.action(description="↩ Mark payment as Refunded")
    def mark_payment_refunded(self, request, queryset):
        updated = queryset.update(payment_status='refunded')
        self.message_user(request, f"{updated} order(s) marked as Refunded.", level=messages.SUCCESS)

    @admin.action(description="🔄 Process Return for selected orders (Restore stock)")
    def process_full_return(self, request, queryset):
        success_count = 0
        for order in queryset:
            if order.status not in ['dispatched', 'delivered', 'partially_returned']:
                self.message_user(request, f"Order {order.order_number} cannot be returned (Current status: {order.status}).", level=messages.WARNING)
                continue
            returns_data = []
            for item in order.items.all():
                remaining_qty = item.quantity - item.returned_quantity
                if remaining_qty > 0:
                    returns_data.append({'order_item_id': item.id, 'quantity': remaining_qty})
            if not returns_data:
                self.message_user(request, f"Order {order.order_number} has no returnable items left.", level=messages.WARNING)
                continue
            try:
                InventoryService.return_order_items(
                    order, returns_data, request.user,
                    reason="Return processed via Django Administration action"
                )
                success_count += 1
            except ValidationError as e:
                self.message_user(request, f"Order {order.order_number}: {e}", level=messages.ERROR)
        if success_count > 0:
            self.message_user(request, f"Successfully processed returns for {success_count} order(s) and restored stock to inventory.", level=messages.SUCCESS)



# -------------------------------------------------------------
# Inventory Transactions Admin
# -------------------------------------------------------------
@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'product_link', 'variant_sku', 'transaction_badge',
        'quantity_display', 'stock_movement', 'order_link',
        'reason', 'created_by', 'created_at'
    )
    search_fields = ('product__title', 'product__sku', 'variant__sku', 'order__order_number', 'reason')
    list_filter = ('transaction_type', 'created_at', 'created_by')
    readonly_fields = (
        'product', 'variant', 'transaction_type', 'quantity',
        'stock_before', 'stock_after', 'order', 'order_item',
        'reason', 'created_by', 'created_at'
    )

    def has_add_permission(self, request):
        return False

    def product_link(self, obj):
        url = reverse('admin:store_product_change', args=[obj.product.id])
        return format_html('<a href="{}" style="font-weight: 600;">{}</a>', url, obj.product.title)
    product_link.short_description = "Product"

    def variant_sku(self, obj):
        return obj.variant.sku if obj.variant else "-"
    variant_sku.short_description = "Variant"

    def transaction_badge(self, obj):
        type_styles = {
            'order_dispatch': ('#f8d7da', '#842029', 'Order Dispatch'),
            'return': ('#d1e7dd', '#0f5132', 'Return Restock'),
            'manual_add': ('#cfe2ff', '#084298', 'Manual Add'),
            'manual_remove': ('#fff3cd', '#664d03', 'Manual Remove'),
            'adjustment': ('#e2e3e5', '#383d41', 'Adjustment'),
        }
        bg, text, label = type_styles.get(obj.transaction_type, ('#e2e3e5', '#383d41', obj.get_transaction_type_display()))
        return format_html(
            '<span style="background: {}; color: {}; padding: 2px 7px; border-radius: 4px; font-weight: 600; font-size: 11px;">{}</span>',
            bg, text, label
        )
    transaction_badge.short_description = "Transaction"

    def quantity_display(self, obj):
        if obj.quantity > 0:
            return format_html('<span style="color: #198754; font-weight: 700;">+{}</span>', obj.quantity)
        return format_html('<span style="color: #dc3545; font-weight: 700;">{}</span>', obj.quantity)
    quantity_display.short_description = "Qty"

    def stock_movement(self, obj):
        return format_html(
            '<span style="color: #6c757d;">{}</span> &rarr; <strong>{}</strong>',
            obj.stock_before, obj.stock_after
        )
    stock_movement.short_description = "Stock Movement"

    def order_link(self, obj):
        if obj.order:
            url = reverse('admin:store_order_change', args=[obj.order.id])
            return format_html('<a href="{}">#{}</a>', url, obj.order.order_number)
        return "-"
    order_link.short_description = "Order"


# -------------------------------------------------------------
# Order Status Log Admin
# -------------------------------------------------------------
@admin.register(OrderStatusLog)
class OrderStatusLogAdmin(admin.ModelAdmin):
    list_display = ('order_link', 'status_transition', 'changed_by', 'note', 'created_at')
    search_fields = ('order__order_number', 'note', 'changed_by__email', 'changed_by__full_name')
    list_filter = ('old_status', 'new_status', 'created_at')
    readonly_fields = ('order', 'old_status', 'new_status', 'changed_by', 'note', 'created_at')

    def has_add_permission(self, request):
        return False

    def order_link(self, obj):
        url = reverse('admin:store_order_change', args=[obj.order.id])
        return format_html('<a href="{}" style="font-weight: 600;">#{}</a>', url, obj.order.order_number)
    order_link.short_description = "Order"

    def status_transition(self, obj):
        old_val = obj.old_status or "New"
        return format_html(
            '<span style="color: #6c757d;">{}</span> &rarr; <span style="font-weight: 600; color: #0d6efd;">{}</span>',
            old_val.upper(), obj.new_status.upper()
        )
    status_transition.short_description = "Status Transition"
