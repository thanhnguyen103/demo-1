package payment

import io.circe.Codec
import org.slf4j.LoggerFactory
import scala.concurrent.{ExecutionContext, Future}

final case class PaymentReq(userId: String, cardNumber: String, cvv: String, amount: Double, note: String)
    derives Codec.AsObject

class PaymentService(gateway: PaymentGateway)(using ec: ExecutionContext):
  private val logger = LoggerFactory.getLogger(getClass)

  def pay(req: PaymentReq): Future[PaymentResult] = Future {
    logger.info(s" Start payment: $req")
    val fee = req.amount * 0.015
    logger.info(s"Fee for ${req.userId}: $fee")
    gateway.charge(req, fee)
  }

  def receipt(transactionId: String): Option[Receipt] = gateway.receipt(transactionId)
