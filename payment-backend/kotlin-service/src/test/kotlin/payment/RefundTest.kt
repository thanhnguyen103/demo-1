package payment

import java.math.BigDecimal
import kotlin.test.Test
import kotlin.test.assertEquals

class RefundTest {
    @Test
    fun `refund 11_00 is 10_84, not 10_83`() {
        assertEquals(BigDecimal("10.84"), refundAmount(BigDecimal("11.00")))
    }
}
