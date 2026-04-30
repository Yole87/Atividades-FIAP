# 🚜 FarmTech Solutions - Visão Computacional para o Agronegócio
**Projeto PBL - Fase 6 (FIAP)**

## 👥 Integrantes do Grupo
* **Alan Santos** - RM 567437
* **Lucas Amorim** - RM 567505

## 🎯 Objetivo do Projeto
A **FarmTech Solutions** visa revolucionar a segurança patrimonial e o monitoramento no agronegócio. Este projeto desenvolve e compara modelos de Visão Computacional (Deep Learning) para a detecção automatizada de maquinário agrícola (Tratores) e animais (Gado) em imagens e vídeos de segurança.

## 🧠 Abordagens Técnicas Avaliadas
Neste repositório (no arquivo `.ipynb`), realizamos a Engenharia de Dados e o treinamento de três abordagens distintas:
1. **YOLOv5 Customizada (Campeã):** Treinamento via *Transfer Learning* (30 vs 60 épocas) adaptado especificamente para o domínio do agro (classes: `trator` e `gado`).
2. **YOLOv5 Padrão (COCO Dataset):** Avaliação de modelo de prateleira, que demonstrou viés de domínio ao confundir tratores com caminhões ("truck").
3. **CNN do Zero (TensorFlow/Keras):** Construção de arquitetura própria que evidenciou problemas de generalização (*Overfitting*) devido ao tamanho reduzido do dataset (64 imagens).

## 🚀 Arquivo Principal
O desenvolvimento completo, os códigos executados, as predições nas imagens de teste e as **Análises Críticas** estão detalhados no notebook Jupyter:
👉 [`AlanSantos_rm567437_LucasAmorim_rm567505_pbl_fase6.ipynb`](./AlanSantos_rm567437_LucasAmorim_rm567505_pbl_fase6.ipynb)

## 📺 Apresentação em Vídeo (Pitch Técnico)
Acompanhe o nosso vídeo de 5 minutos, onde apresentamos os resultados na prática, os desafios de infraestrutura enfrentados (limitações de GPU/RAM) e a conclusão sobre a melhor arquitetura para o cliente FarmTech:

🔗 **[[Video do YouTube](https://youtu.be/e8LMRWNYyzA)]**