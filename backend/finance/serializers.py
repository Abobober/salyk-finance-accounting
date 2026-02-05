from rest_framework import serializers
from .models import Category, Transaction
from django.db.models import Q



class CategorySerializer(serializers.ModelSerializer):
    category_type_display = serializers.CharField(source='get_category_type_display', read_only=True)

    class Meta:
        model = Category
        fields = (
            'id',
            'name',
            'category_type',
            'category_type_display',
            'is_system',
            'created_at',
        )
        read_only_fields = ('id', 'is_system', 'created_at')


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Transaction
        fields = (
            'id',
            'amount',
            'transaction_type',
            'category',
            'category_name',
            'description',
            'transaction_date',
            'created_at',
        )
        read_only_fields = ('id', 'created_at')
        
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            user = request.user
            self.fields['category'].queryset = Category.objects.filter(
                Q(user=user) | Q(is_system=True)
            )
        else:
            self.fields['category'].queryset = Category.objects.filter(is_system=True)
    
    def validate(self, attrs):
        
        category = attrs.get('category')
        t_type = attrs.get('transaction_type')

        if not t_type and self.instance:
            t_type = self.instance.transaction_type
        if not category and self.instance:
            category = self.instance.category

        if category and t_type and category.category_type != t_type:
            raise serializers.ValidationError({
                'category': f"Тип категории ({category.get_category_type_display()}) не совпадает с типом операции ({t_type})"
            })
        
        return attrs
