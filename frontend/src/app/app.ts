import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { PaymentReceiptComponent } from './payment-receipt/payment-receipt.component';

interface PaymentResult {
  transactionId: string;
  status: string;
  amount: number;
  fee: number;
  total: number;
}

@Component({
  selector: 'app-root',
  imports: [FormsModule, PaymentReceiptComponent],
  templateUrl: './app.html',
  styleUrl: './app.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {
  private readonly http = inject(HttpClient);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly form = {
    userId: 'u-1001',
    cardNumber: '4111111111111234',
    cvv: '123',
    amount: 10.05,
    note: 'Cảm ơn shop!',
  };
  protected readonly result = signal<PaymentResult | null>(null);
  protected readonly error = signal('');
  protected readonly paying = signal(false);

  protected pay(): void {
    this.paying.set(true);
    this.error.set('');
    this.http
      .post<PaymentResult>('/api/payments', this.form)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (r) => {
          this.result.set(r);
          this.paying.set(false);
        },
        error: () => {
          this.error.set('Thanh toán thất bại — backend có đang chạy không?');
          this.paying.set(false);
        },
      });
  }
}
