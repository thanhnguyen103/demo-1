package payment

import java.util.UUID
import java.util.concurrent.ConcurrentHashMap

data class PaymentResult(
    val transactionId: String,
    val status: String,
    val amount: Double,
    val fee: Double,
    val total: Double,
)

data class Receipt(val transactionId: String, val receiptHtml: String)

interface PaymentGateway {
    fun charge(req: PaymentReq, fee: Double): PaymentResult
    fun receipt(transactionId: String): Receipt?
}

/** Stands in for a vendor SDK: blocking HTTP call that returns an HTML receipt. */
class FakePaymentGateway : PaymentGateway {
    private val receipts = ConcurrentHashMap<String, Receipt>()

    override fun charge(req: PaymentReq, fee: Double): PaymentResult {
        Thread.sleep(300)
        val result = PaymentResult(UUID.randomUUID().toString(), "APPROVED", req.amount, fee, req.amount + fee)
        receipts[result.transactionId] = Receipt(
            result.transactionId,
            """
            <p><b>Thanh toán thành công</b></p>
            <p>Mã GD: ${result.transactionId}</p>
            <p>Tổng tiền: $${result.total}</p>
            <p>Ghi chú: ${req.note}</p>
            """.trimIndent(),
        )
        return result
    }

    override fun receipt(transactionId: String): Receipt? = receipts[transactionId]
}
