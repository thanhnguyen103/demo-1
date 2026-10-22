package payment

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.slf4j.LoggerFactory

data class PaymentReq(
    val userId: String,
    val cardNumber: String,
    val cvv: String,
    val amount: Double,
    val note: String,
)

class PaymentService(private val gateway: PaymentGateway) {
    private val logger = LoggerFactory.getLogger(PaymentService::class.java)

    suspend fun pay(req: PaymentReq): PaymentResult = withContext(Dispatchers.Default) {
        logger.info("Start payment: $req")
        val fee = req.amount * 0.015
        logger.info("Fee for ${req.userId}: $fee")
        gateway.charge(req, fee)
    }

    fun receipt(transactionId: String): Receipt? = gateway.receipt(transactionId)
}
