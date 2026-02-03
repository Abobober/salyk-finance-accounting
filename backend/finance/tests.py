from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from finance.models import Category, Transaction
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

class FinanceAPITestCase(APITestCase):

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=self.user)

        # Create some test data
        self.category = Category.objects.create(name='Food', type='expense')
        self.transaction = Transaction.objects.create(
            amount=Decimal('12.34'),
            category=self.category,
            description='Lunch'
        )

    # ---------- Category Tests ----------
    def test_list_categories(self):
        url = reverse('category-list')  # DRF Default router name
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_category(self):
        url = reverse('category-list')
        data = {"name": "Salary", "type": "income"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 2)

    def test_retrieve_category(self):
        url = reverse('category-detail', args=[self.category.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Food')

    def test_update_category(self):
        url = reverse('category-detail', args=[self.category.id])
        data = {"name": "Groceries", "type": "expense"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Groceries')

    def test_delete_category(self):
        url = reverse('category-detail', args=[self.category.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 0)

    # ---------- Transaction Tests ----------
    def test_list_transactions(self):
        url = reverse('transaction-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_transaction(self):
        url = reverse('transaction-list')
        data = {
            "amount": "50.00",
            "category": self.category.id,
            "description": "Dinner"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 2)

    def test_retrieve_transaction(self):
        url = reverse('transaction-detail', args=[self.transaction.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Lunch')

    def test_update_transaction(self):
        url = reverse('transaction-detail', args=[self.transaction.id])
        data = {
            "amount": "15.00",
            "category": self.category.id,
            "description": "Lunch updated"
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.transaction.refresh_from_db()
        self.assertEqual(str(self.transaction.amount), "15.00")
        self.assertEqual(self.transaction.description, "Lunch updated")

    def test_delete_transaction(self):
        url = reverse('transaction-detail', args=[self.transaction.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Transaction.objects.count(), 0)
