package payment

import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import io.ktor.client.request.get
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.HttpStatusCode
import io.ktor.http.contentType
import io.ktor.server.testing.testApplication
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class PaymentApiTest {
    @Test
    fun `pay then fetch receipt`() = testApplication {
        application { module() }

        val pay = client.post("/api/payments") {
            contentType(ContentType.Application.Json)
            setBody("""{"userId":"u-1","cardNumber":"4111111111111234","cvv":"123","amount":10.05,"note":"hi"}""")
        }
        assertEquals(HttpStatusCode.OK, pay.status)
        val body = jacksonObjectMapper().readTree(pay.bodyAsText())
        assertEquals("APPROVED", body["status"].asText())

        val receipt = client.get("/api/payments/${body["transactionId"].asText()}/receipt")
        assertEquals(HttpStatusCode.OK, receipt.status)
        assertTrue(receipt.bodyAsText().contains("Thanh toán thành công"))
    }

    @Test
    fun `unknown receipt is 404`() = testApplication {
        application { module() }
        assertEquals(HttpStatusCode.NotFound, client.get("/api/payments/nope/receipt").status)
    }
}
