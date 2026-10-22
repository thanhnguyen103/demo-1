import { Component, Input, OnChanges, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

interface PaymentResponse {
  transactionId: string;
  receiptHtml: string;
}

@Component({
  selector: 'app-payment-receipt',
  template: `
    <h2>Biên nhận thanh toán</h2>
    <div [innerHTML]="receipt()"></div>
  `,
})
export class PaymentReceiptComponent implements OnChanges {
  @Input() transactionId = '';
  receipt = signal<SafeHtml>('');

  constructor(private http: HttpClient, private sanitizer: DomSanitizer) {}

  ngOnChanges(): void {
    this.http
      .get<PaymentResponse>(`/api/payments/${this.transactionId}/receipt`)
      .subscribe((response) => {
        this.receipt.set(this.sanitizer.bypassSecurityTrustHtml(response.receiptHtml));
      });
  }
}
