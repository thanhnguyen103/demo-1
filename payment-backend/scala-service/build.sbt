ThisBuild / scalaVersion := "3.3.8"

val circeVersion = "0.14.17"

lazy val root = (project in file("."))
  .settings(
    name := "scala-payment-service",
    libraryDependencies ++= Seq(
      "io.circe" %% "circe-core" % circeVersion,
      "io.circe" %% "circe-parser" % circeVersion,
      "ch.qos.logback" % "logback-classic" % "1.6.5",
      "org.scalameta" %% "munit" % "1.3.6" % Test
    ),
    run / fork := true
  )
