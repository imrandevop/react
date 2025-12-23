from django.contrib import admin
from .models import User, Post, PostImage, Vote, Comment, PostReport

class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1

class PostAdmin(admin.ModelAdmin):
    inlines = [PostImageInline]
    list_display = ('id', 'user', 'category', 'headline', 'pincode', 'is_ad_approved', 'created_at')
    list_filter = ('category', 'is_ad_approved', 'pincode')
    search_fields = ('description', 'headline', 'user__localBody', 'sponsor_name')
    
    # Enable editing of ad fields
    fieldsets = (
        (None, {
            'fields': ('user', 'category', 'headline', 'description', 'pincode')
        }),
        ('Ad Details', {
            'classes': ('collapse',),
            'fields': ('is_ad_approved', 'sponsor_name', 'button_text', 'button_url'),
        }),
    )

class PostReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('description', 'post__description', 'user__localBody')
    readonly_fields = ('post', 'user', 'created_at')

    fieldsets = (
        (None, {
            'fields': ('post', 'user', 'description', 'created_at')
        }),
        ('Moderation', {
            'fields': ('status',),
        }),
    )

admin.site.register(User)
admin.site.register(Post, PostAdmin)
admin.site.register(Vote)
admin.site.register(Comment)
admin.site.register(PostReport, PostReportAdmin)
