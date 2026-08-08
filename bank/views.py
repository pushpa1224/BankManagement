import csv
import random
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Sum
from .models import BankAccount, Transaction
from .forms import UserRegistrationForm, BankAccountForm, DepositForm, WithdrawForm

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'bank/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Login successful.')
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'bank/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have successfully logged out.')
    return redirect('login')

@login_required
def dashboard_view(request):
    try:
        account = request.user.bankaccount
    except BankAccount.DoesNotExist:
        return redirect('create_account')
    
    total_deposits = account.transactions.filter(transaction_type='DEPOSIT').aggregate(Sum('amount'))['amount__sum'] or 0
    total_withdrawals = account.transactions.filter(transaction_type='WITHDRAWAL').aggregate(Sum('amount'))['amount__sum'] or 0
    total_transactions = account.transactions.count()
    
    context = {
        'account': account,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'total_transactions': total_transactions
    }
    return render(request, 'bank/dashboard.html', context)

@login_required
def create_account_view(request):
    if hasattr(request.user, 'bankaccount'):
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = BankAccountForm(request.POST)
        if form.is_valid():
            bank_account = form.save(commit=False)
            bank_account.user = request.user
            bank_account.account_number = str(random.randint(1000000000, 9999999999))
            bank_account.save()
            messages.success(request, 'Bank account created successfully.')
            return redirect('dashboard')
    else:
        form = BankAccountForm()
    return render(request, 'bank/create_account.html', {'form': form})

@login_required
def deposit_view(request):
    try:
        account = request.user.bankaccount
    except BankAccount.DoesNotExist:
        return redirect('create_account')

    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            account.balance += amount
            account.save()
            
            Transaction.objects.create(
                account=account,
                transaction_type='DEPOSIT',
                amount=amount,
                balance_after_transaction=account.balance
            )
            messages.success(request, f'Successfully deposited ${amount}.')
            return redirect('dashboard')
    else:
        form = DepositForm()
    return render(request, 'bank/deposit.html', {'form': form})

@login_required
def withdraw_view(request):
    try:
        account = request.user.bankaccount
    except BankAccount.DoesNotExist:
        return redirect('create_account')

    if request.method == 'POST':
        form = WithdrawForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if amount > account.balance:
                messages.error(request, 'Insufficient funds. Overdraft prevented.')
            else:
                account.balance -= amount
                account.save()
                
                Transaction.objects.create(
                    account=account,
                    transaction_type='WITHDRAWAL',
                    amount=amount,
                    balance_after_transaction=account.balance
                )
                messages.success(request, f'Successfully withdrew ${amount}.')
                return redirect('dashboard')
    else:
        form = WithdrawForm()
    return render(request, 'bank/withdraw.html', {'form': form})

@login_required
def transaction_history_view(request):
    try:
        account = request.user.bankaccount
    except BankAccount.DoesNotExist:
        return redirect('create_account')

    transactions = account.transactions.all().order_by('-timestamp')
    
    transaction_type = request.GET.get('transaction_type')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
        
    if from_date:
        transactions = transactions.filter(timestamp__date__gte=from_date)
        
    if to_date:
        transactions = transactions.filter(timestamp__date__lte=to_date)
        
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transaction_history.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Type', 'Amount', 'Date & Time', 'Balance After'])
        
        for transaction in transactions:
            writer.writerow([
                transaction.get_transaction_type_display(),
                transaction.amount,
                transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                transaction.balance_after_transaction
            ])
            
        return response
        
    return render(request, 'bank/transaction_history.html', {'transactions': transactions})
