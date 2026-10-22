package payment

import io.circe.Codec
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap

final case class PaymentResult(transactionId: String, status: String, amount: Double, fee: Double, total: Double)
    derives Codec.AsObject

final case class Receipt(transactionId: String, receiptHtml: String) derives Codec.AsObject

trait PaymentGateway:
  def charge(req: PaymentReq, fee: Double): PaymentResult
  def receipt(transactionId: String): Option[Receipt]

/** Stands in for a vendor SDK: blocking HTTP call that returns an HTML receipt. */
class FakePaymentGateway extends PaymentGateway:
  private val receipts = ConcurrentHashMap[String, Receipt]()

  def charge(req: PaymentReq, fee: Double): PaymentResult =
    Thread.sleep(300)
    val result = PaymentResult(UUID.randomUUID().toString, "APPROVED", req.amount, fee, req.amount + fee)
    receipts.put(
      result.transactionId,
      Receipt(
        result.transactionId,
        s"""<p><b>Thanh toán thành công</b></p>
           |<p>Mã GD: ${result.transactionId}</p>
           |<p>Tổng tiền: $$${result.total}</p>
           |<p>Ghi chú: ${req.note}</p>""".stripMargin
      )
    )
    result

  def receipt(transactionId: String): Option[Receipt] = Option(receipts.get(transactionId))
