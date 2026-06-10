# =============================
# Clima via Open-Meteo (sem token)
# Salve como: clima.R
# Execute no R/RStudio: source("clima.R")
# ou pela linha de comando: Rscript Clima.R "São Paulo"
# =============================

# Pacotes necessários
packages <- c("httr", "jsonlite")
new <- packages[!(packages %in% installed.packages()[, "Package"])]
if(length(new)) install.packages(new, repos = "https://cloud.r-project.org")
library(httr)
library(jsonlite)

# ---------- Funções auxiliares ----------
geocode_city <- function(city) {
  url <- paste0(
    "https://geocoding-api.open-meteo.com/v1/search?name=",
    URLencode(city, reserved = TRUE),
    "&count=1&language=pt&format=json"
  )
  res <- GET(url)
  if (http_error(res)) stop("Falha ao geocodificar a cidade.")
  data <- fromJSON(content(res, as = "text", encoding = "UTF-8"))
  if (is.null(data$results) || nrow(data$results) == 0) {
    stop("Cidade não encontrada na geocodificação.")
  }
  list(
    name = data$results$name[1],
    country = data$results$country[1],
    lat = data$results$latitude[1],
    lon = data$results$longitude[1],
    timezone = data$results$timezone[1]
  )
}

fetch_weather <- function(lat, lon, tz = "auto") {
  # hourly: temperatura, umidade, precipitação
  # daily: min/max e precipitação total
  url <- paste0(
    "https://api.open-meteo.com/v1/forecast?",
    "latitude=", lat,
    "&longitude=", lon,
    "&hourly=temperature_2m,relative_humidity_2m,precipitation",
    "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum",
    "&current_weather=true",
    "&timezone=", tz
  )
  res <- GET(url)
  if (http_error(res)) stop("Falha ao consultar a API meteorológica.")
  fromJSON(content(res, as = "text", encoding = "UTF-8"), flatten = TRUE)
}

print_report <- function(place, wx) {
  cat("\n================ CLIMA – Open-Meteo ================\n")
  cat("Local: ", place$name, " - ", place$country, "\n", sep = "")
  cat("Coordenadas: ", round(place$lat, 4), ", ", round(place$lon, 4),
      " | Timezone: ", place$timezone, "\n", sep = "")
  cat("====================================================\n\n")
  
  # Atual
  if (!is.null(wx$current_weather)) {
    cw <- wx$current_weather
    cat("⏱️ Agora\n")
    cat("  Temperatura: ", cw$temperature, " °C\n", sep = "")
    cat("  Vento: ", cw$windspeed, " km/h | Direção: ", cw$winddirection, "°\n", sep = "")
    cat("  Código do tempo (WMO): ", cw$weathercode, "\n\n", sep = "")
  }
  
  # Diária (hoje)
  if (!is.null(wx$daily)) {
    d <- wx$daily
    cat("📅 Hoje\n")
    cat("  Mín/Máx: ", d$temperature_2m_min[1], "°C / ",
        d$temperature_2m_max[1], "°C\n", sep = "")
    cat("  Precipitação (total): ", d$precipitation_sum[1], " mm\n\n", sep = "")
  }
  
  # Horária – últimas 24h (média/estatísticas simples)
  if (!is.null(wx$hourly)) {
    h <- wx$hourly
    # pega últimas 24 entradas (se houver)
    n <- length(h$time)
    take <- min(24, n)
    idx <- (n - take + 1):n
    
    temp24 <- h$temperature_2m[idx]
    umid24 <- h$relative_humidity_2m[idx]
    prec24 <- h$precipitation[idx]
    
    cat("📈 Últimas ", take, " horas (estatísticas)\n", sep = "")
    cat("  Temp média: ", round(mean(temp24, na.rm = TRUE), 2), " °C\n", sep = "")
    cat("  Umidade média: ", round(mean(umid24, na.rm = TRUE), 1), " %\n", sep = "")
    cat("  Precipitação acumulada: ", round(sum(prec24, na.rm = TRUE), 2), " mm\n\n", sep = "")
  }
  
  cat("====================================================\n")
}

# ---------- Execução ----------
# cidade por argumento de linha de comando ou padrão
args <- commandArgs(trailingOnly = TRUE)
cidade <- if (length(args) >= 1) args[1] else "São Paulo"

# Fluxo
tryCatch({
  place <- geocode_city(cidade)
  wx <- fetch_weather(place$lat, place$lon, tz = place$timezone)
  print_report(place, wx)
}, error = function(e) {
  message("Erro: ", e$message)
  quit(status = 1)
})