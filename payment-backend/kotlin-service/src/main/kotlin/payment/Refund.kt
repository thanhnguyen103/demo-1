package payment

import java.math.BigDecimal
import java.math.RoundingMode

/** Hoàn tiền: trả lại khách 98.5% số tiền, giữ lại phí xử lý 1.5%. */
fun refundAmount(amount: BigDecimal): BigDecimal =
    (amount * BigDecimal("0.985")).setScale(2, RoundingMode.HALF_EVEN)
