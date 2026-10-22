package payment

import scala.concurrent.ExecutionContext

class PaymentServiceSuite extends munit.FunSuite:
  given ExecutionContext = ExecutionContext.global

  test("pay then fetch receipt") {
    val service = PaymentService(FakePaymentGateway())
    service.pay(PaymentReq("u-1", "4111111111111234", "123", 10.05, "hi")).map { result =>
      assertEquals(result.status, "APPROVED")
      assert(service.receipt(result.transactionId).exists(_.receiptHtml.contains("Thanh toán thành công")))
    }
  }

  test("unknown receipt is None") {
    assertEquals(PaymentService(FakePaymentGateway()).receipt("nope"), None)
  }
