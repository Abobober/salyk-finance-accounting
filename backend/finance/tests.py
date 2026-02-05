from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.management import call_command
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Category, Transaction

User = get_user_model()

class FinanceAPITests(APITestCase):

    def setUp(self):
        # 1. Наполняем тестовую БД системными категориями через вашу команду
        call_command('setup_categories')
        
        # 2. Создаем пользователей
        self.user = User.objects.create_user(email='testuser@gmail.com', password='password123')
        self.other_user = User.objects.create_user(email='otheruser@gmail.com', password='password123')
        
        # 3. Находим системную категорию (она уже создана командой выше)
        self.system_category = Category.objects.get(name="Налоги", is_system=True)
        
        # 4. Создаем личную категорию пользователя
        self.user_category = Category.objects.create(
            name="Еда", 
            category_type=Category.CategoryType.EXPENSE, 
            user=self.user
        )

        # 5. Категория другого пользователя (для проверки изоляции)
        self.other_user_category = Category.objects.create(
            name="Чужая заначка", 
            category_type=Category.CategoryType.INCOME, 
            user=self.other_user
        )

        self.client.force_authenticate(user=self.user)

    def get_data_from_response(self, response):
        """Вспомогательный метод для обработки пагинации."""
        if isinstance(response.data, dict) and 'results' in response.data:
            return response.data['results']
        return response.data

    # --- ТЕСТЫ КАТЕГОРИЙ ---

    def test_get_categories_list(self):
        """Проверка, что пользователь видит свои и системные категории, но не чужие."""
        url = reverse('category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = self.get_data_from_response(response)
        names = [item['name'] for item in data]
        
        # Должно быть: 16 системных + 1 личная ('Еда')
        self.assertTrue(len(names) >= 17)
        self.assertIn("Налоги", names)
        self.assertIn("Еда", names)
        self.assertNotIn("Чужая заначка", names)

    def test_create_category(self):
        """Проверка автоматической привязки пользователя при создании категории."""
        url = reverse('category-list')
        data = {"name": "Хобби", "category_type": "expense"}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        category = Category.objects.get(id=response.data['id'])
        self.assertEqual(category.user, self.user)

    # --- ТЕСТЫ ТРАНЗАКЦИЙ ---

    def test_create_transaction_type_mismatch(self):
        """Ошибка, если тип транзакции не совпадает с типом категории."""
        url = reverse('transaction-list')
        data = {
            "amount": "100.00",
            "transaction_type": "income",  # Доход
            "category": self.user_category.id,  # Категория 'Еда' (Расход)
            "transaction_date": "2026-02-05"
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category', response.data)

    def test_prevent_using_others_category(self):
        """Нельзя использовать категорию другого пользователя."""
        url = reverse('transaction-list')
        data = {
            "amount": "500.00",
            "transaction_type": "income",
            "category": self.other_user_category.id,
            "transaction_date": "2026-02-05"
        }
        response = self.client.post(url, data)
        
        # Должна быть ошибка 400, так как категория не найдена в доступных юзеру
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transaction_summary_by_category(self):
        """Проверка агрегации суммы по категориям."""
        Transaction.objects.create(
            user=self.user, amount=500, transaction_type="expense",
            category=self.user_category, transaction_date="2026-02-05"
        )
        Transaction.objects.create(
            user=self.user, amount=300, transaction_type="expense",
            category=self.user_category, transaction_date="2026-02-05"
        )
        
        url = reverse('transaction-summary-by-category')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Ищем объект с названием нашей категории
        summary_item = next(item for item in response.data if item['category__name'] == "Еда")
        self.assertEqual(float(summary_item['total']), 800.00)

    def test_transaction_filter_by_date(self):
        """Проверка работы фильтров даты."""
        Transaction.objects.create(
            user=self.user, amount=10, transaction_type="expense",
            transaction_date="2025-01-01"
        )
        Transaction.objects.create(
            user=self.user, amount=20, transaction_type="expense",
            transaction_date="2026-01-01"
        )
        
        url = reverse('transaction-list')
        # Фильтруем "до середины 2025 года"
        response = self.client.get(url, {'date_to': '2025-06-01'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = self.get_data_from_response(response)
        
        self.assertEqual(len(data), 1)
        self.assertEqual(float(data[0]['amount']), 10.00)

    def test_delete_system_category_forbidden(self):
        """Запрет на удаление системных категорий."""
        url = reverse('category-detail', args=[self.system_category.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
