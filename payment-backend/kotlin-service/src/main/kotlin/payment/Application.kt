package payment

import io.ktor.http.HttpStatusCode
import io.ktor.serialization.jackson.jackson
import io.ktor.server.application.Application
import io.ktor.server.application.install
import io.ktor.server.engine.embeddedServer
import io.ktor.server.netty.Netty
import io.ktor.server.plugins.contentnegotiation.ContentNegotiation
import io.ktor.server.request.receive
import io.ktor.server.response.respond
import io.ktor.server.routing.get
import io.ktor.server.routing.post
import io.ktor.server.routing.routing

fun main() {
    val port = System.getenv("PORT")?.toInt() ?: 8081
    embeddedServer(Netty, port = port) { module() }.start(wait = true)
}

fun Application.module(service: PaymentService = PaymentService(FakePaymentGateway())) {
    install(ContentNegotiation) { jackson() }

    routing {
        post("/api/payments") {
            call.respond(service.pay(call.receive<PaymentReq>()))
        }
        get("/api/payments/{id}/receipt") {
            val receipt = service.receipt(call.parameters["id"]!!)
            if (receipt == null) call.respond(HttpStatusCode.NotFound) else call.respond(receipt)
        }
    }
}
