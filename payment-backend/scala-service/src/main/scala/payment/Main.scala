package payment

import com.sun.net.httpserver.{HttpExchange, HttpServer}
import io.circe.parser.decode
import io.circe.syntax.*
import java.net.InetSocketAddress
import java.nio.charset.StandardCharsets.UTF_8
import scala.concurrent.ExecutionContext
import scala.util.{Failure, Success}

@main def run(): Unit =
  given ExecutionContext = ExecutionContext.global
  val port = sys.env.get("PORT").map(_.toInt).getOrElse(8082)
  val service = PaymentService(FakePaymentGateway())
  val server = HttpServer.create(InetSocketAddress(port), 0)
  server.createContext("/api/payments", exchange => route(service, exchange))
  server.start()
  println(s"Scala payment service listening on :$port")

private val ReceiptPath = "/api/payments/([^/]+)/receipt".r

def route(service: PaymentService, ex: HttpExchange)(using ExecutionContext): Unit =
  (ex.getRequestMethod, ex.getRequestURI.getPath) match
    case ("POST", "/api/payments") =>
      decode[PaymentReq](String(ex.getRequestBody.readAllBytes(), UTF_8)) match
        case Left(err) => respond(ex, 400, s"""{"error":"${err.getMessage}"}""")
        case Right(req) =>
          service.pay(req).onComplete {
            case Success(result) => respond(ex, 200, result.asJson.noSpaces)
            case Failure(e)      => respond(ex, 500, s"""{"error":"${e.getMessage}"}""")
          }
    case ("GET", ReceiptPath(id)) =>
      service.receipt(id) match
        case Some(r) => respond(ex, 200, r.asJson.noSpaces)
        case None    => respond(ex, 404, """{"error":"not found"}""")
    case _ => respond(ex, 404, """{"error":"not found"}""")

private def respond(ex: HttpExchange, status: Int, json: String): Unit =
  val bytes = json.getBytes(UTF_8)
  ex.getResponseHeaders.set("Content-Type", "application/json")
  ex.sendResponseHeaders(status, bytes.length)
  ex.getResponseBody.write(bytes)
  ex.close()
