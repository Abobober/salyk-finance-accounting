from rest_framework import serializers
from .models import Transaction, Category


class CategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для категорий.
    Преобразует объект Category в JSON и обратно.
    """
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'category_type', 'is_system', 'created_at']
        read_only_fields = ['id', 'is_system', 'created_at']
    
    def create(self, validated_data):
        """
        При создании категории автоматически привязываем ее к текущему пользователю.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    """
    Сериализатор для транзакций.
    Преобразует объект Transaction в JSON и обратно.
    """
    
    # Включаем полную информацию о категории, а не только ID
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    # Добавляем поле для отображения типа операции текстом
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True
    )
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'transaction_type',
            'transaction_type_display',
            'category',
            'category_id',
            'amount',
            'description',
            'transaction_date',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """
        Проверяем корректность данных перед сохранением.
        """
        # Проверяем, что сумма положительная
        if data.get('amount') <= 0:
            raise serializers.ValidationError({
                "amount": "Сумма должна быть больше нуля"
            })
        
        # Проверяем, что категория соответствует типу операции
        category = data.get('category')
        transaction_type = data.get('transaction_type')
        
        if category and category.category_type != transaction_type:
            raise serializers.ValidationError({
                "category": f"Категория '{category.name}' предназначена для "
                          f"{category.get_category_type_display()}, а не для "
                          f"{dict(Transaction.TRANSACTION_TYPES).get(transaction_type)}"
            })
        
        return data
    
    def create(self, validated_data):
        """
        При создании транзакции автоматически привязываем ее к текущему пользователю.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        
        # Если категория не указана, можно было бы использовать автокатегоризацию
        # (реализуем в MVP 2)
        return super().create(validated_data)


class TransactionSummarySerializer(serializers.Serializer):
    """
    Сериализатор для сводки по транзакциям.
    Используется для отображения итогов.
    """
    total_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_expense = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    transaction_count = serializers.IntegerField()