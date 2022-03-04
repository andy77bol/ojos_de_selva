from django.contrib import admin
from import_export.admin import ImportExportMixin
from import_export.admin import ImportExportModelAdmin

from .models import Item, OrderItem, Order, Customer, Project
from allauth.socialaccount.models import SocialToken, SocialAccount, SocialApp, EmailAddress


def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=False, refund_granted=True)


make_refund_accepted.short_description = 'Update orders to refund granted'


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'customer',
        'get_order_items',
        'ordered',
        'department'
    ]
    list_display_links = [
        'customer'
    ]
    list_filter = ['ordered']

    filter_horizontal = ('items', )  # this shows on the right only the ordered items
    search_fields = [
        'user__username',
        'ref_code'
    ]
    actions = [make_refund_accepted]


class CustomerAdmin(ImportExportModelAdmin):
    list_display = [
        'name',
        'phone'
    ]


class ProjectAdmin(ImportExportModelAdmin):
    list_display = [
        'title',
        'month',
        'year'
    ]


class ItemAdmin(ImportExportModelAdmin):
    list_display = [
        'title'
    ]


admin.site.register(Item, ItemAdmin)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.unregister(SocialToken)
admin.site.unregister(SocialAccount)
admin.site.unregister(SocialApp)
admin.site.unregister(EmailAddress)
