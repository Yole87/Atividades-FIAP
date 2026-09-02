# Lê o arquivo CSV
dados <- read.csv("farmtech_export.csv", sep = ",", header = TRUE)

# Mostra os dados importados
print(dados)

# Calcula a média da coluna area_total
media_area <- mean(dados$area_total)
cat("Média da área total:", media_area, "\n")

# Calcula o desvio padrão da coluna area_total
desvio_area <- sd(dados$area_total)
cat("Desvio padrão da área total:", desvio_area, "\n")
