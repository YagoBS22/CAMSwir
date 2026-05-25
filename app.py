import os
import cv2
import numpy as np
import pandas as pd
import time
import ctypes

from arena_api.system import system
from arena_api.buffer import BufferFactory

# CALIBRAGEM E REFERÊNCIAS
def carregar_referencias(pasta_ref):
    refs = {}
    formatos = ('.jpg', '.jpeg', '.png', '.bmp')
    
    if not os.path.exists(pasta_ref):
        os.makedirs(pasta_ref)
        print(f"Pasta '{pasta_ref}' criada. Adicione imagens de calibração lá no futuro.")
        return refs

    for arq in os.listdir(pasta_ref):
        if arq.lower().endswith(formatos):
            caminho = os.path.join(pasta_ref, arq)
            img = cv2.imread(caminho, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                brilho = round(float(np.mean(img)), 2)
                refs[arq] = brilho
                
    print(f"[{len(refs)}] imagens de referência carregadas.")
    return refs

def encontrar_melhor_referencia(brilho_campo, refs):
    if not refs:
        return "Sem referência", 0.0, 0.0
        
    nome_ref = min(refs.keys(), key=lambda k: abs(refs[k] - brilho_campo))
    brilho_ref = refs[nome_ref]
    diferenca = round(abs(brilho_campo - brilho_ref), 2)
    
    return nome_ref, brilho_ref, diferenca

# MODO: CÂMERA AO VIVO
def modo_camera(pasta_ref, pasta_comp):
    print("\nIniciando conexão com a câmera Atlas SWIR...")
    
    if not os.path.exists(pasta_comp):
        os.makedirs(pasta_comp)

    refs = carregar_referencias(pasta_ref)
    resultados = []
    contador_fotos = 1

    tries, tries_max, sleep_time_secs = 0, 6, 5
    device = None
    while tries < tries_max:
        devices = system.create_device()
        if not devices:
            print(f'Aguardando câmera... (Tentativa {tries+1}/{tries_max})')
            time.sleep(sleep_time_secs)
            tries += 1
        else:
            device = system.select_device(devices)
            break
            
    if not device:
        print("Erro: Câmera SWIR não encontrada na rede.")
        return

    nodemap = device.nodemap
    nodes = nodemap.get_node(['Width', 'Height', 'PixelFormat'])
    nodes['PixelFormat'].value = 'Mono8'
    device.tl_stream_nodemap["StreamBufferHandlingMode"].value = "NewestOnly"
    num_channels = 1

    print("\n" + "="*50)
    print(" MODO CÂMERA INICIADO")
    print(" Pressione 'C' para tirar uma foto e medir.")
    print(" Pressione 'ESC' para sair e salvar a planilha.")
    print("="*50 + "\n")

    with device.start_stream():
        while True:
            buffer = device.get_buffer()
            item = BufferFactory.copy(buffer)
            device.requeue_buffer(buffer)

            buffer_bytes_per_pixel = int(len(item.data)/(item.width * item.height))
            array = (ctypes.c_ubyte * num_channels * item.width * item.height).from_address(ctypes.addressof(item.pbytes))
            npndarray = np.ndarray(buffer=array, dtype=np.uint8, shape=(item.height, item.width, buffer_bytes_per_pixel))
            
            np_gray = npndarray.reshape((item.height, item.width))
            heatmap = cv2.applyColorMap(np_gray, cv2.COLORMAP_INFERNO)
            
            cv2.putText(heatmap, "Ao vivo (Aperte 'C' para Capturar)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.imshow('Inspecao SWIR', heatmap)

            BufferFactory.destroy(item)

            key = cv2.waitKey(1)
            if key == ord('c') or key == ord('C'):
                brilho_campo = round(float(np.mean(np_gray)), 2)
                nome_ref, brilho_ref, diferenca = encontrar_melhor_referencia(brilho_campo, refs)
                
                nome_arquivo = f"amostra_campo_{contador_fotos:03d}.png"
                cv2.imwrite(os.path.join(pasta_comp, nome_arquivo), heatmap)
                
                resultados.append({
                    "Origem": "Câmera Ao Vivo",
                    "Arquivo": nome_arquivo,
                    "Brilho (Raw)": brilho_campo,
                    "Referência Mais Próxima": nome_ref,
                    "Brilho da Ref": brilho_ref,
                    "Diferença": diferenca
                })
                print(f"Foto: {nome_arquivo} | Brilho: {brilho_campo} | Ref: {nome_ref} (Dif: {diferenca})")
                
                cv2.imshow('Inspecao SWIR', 255 * np.ones_like(heatmap))
                cv2.waitKey(100)
                contador_fotos += 1

            elif key == 27:
                break
                
        device.stop_stream()
        cv2.destroyAllWindows()
    system.destroy_device()
    
    gerar_relatorio(resultados, "relatorio_swir_camera.xlsx")

# MODO: PROCESSAR PASTA LOCAL COM COMPARAÇÃO VISUAL
def modo_pasta(pasta_ref, pasta_comp):
    print("\nIniciando processamento em lote da pasta...")
    
    if not os.path.exists(pasta_comp):
        print(f"Erro: A pasta '{pasta_comp}' não existe. Crie-a e coloque as imagens lá.")
        return

    refs = carregar_referencias(pasta_ref)
    resultados = []
    formatos = ('.jpg', '.jpeg', '.png', '.bmp')

    arquivos = [arq for arq in os.listdir(pasta_comp) if arq.lower().endswith(formatos)]
    
    if not arquivos:
        print(f"Nenhuma imagem encontrada na pasta '{pasta_comp}'.")
        return

    print("\n" + "="*50)
    print(" COMPARAÇÃO VISUAL INICIADA")
    print(" Pressione a 'BARRA DE ESPAÇO' para ver a próxima imagem.")
    print(" Pressione 'ESC' a qualquer momento para sair e gerar o relatório.")
    print("="*50 + "\n")

    for arq in arquivos:
        caminho_campo = os.path.join(pasta_comp, arq)
        img_campo = cv2.imread(caminho_campo, cv2.IMREAD_GRAYSCALE)
        
        if img_campo is not None:
            brilho_campo = round(float(np.mean(img_campo)), 2)
            nome_ref, brilho_ref, diferenca = encontrar_melhor_referencia(brilho_campo, refs)
            
            resultados.append({
                "Origem": "Pasta Local",
                "Arquivo": arq,
                "Brilho (Raw)": brilho_campo,
                "Referência Mais Próxima": nome_ref,
                "Brilho da Ref": brilho_ref,
                "Diferença": diferenca
            })
            
            caminho_ref = os.path.join(pasta_ref, nome_ref)
            img_ref = cv2.imread(caminho_ref, cv2.IMREAD_GRAYSCALE)
            
            if img_ref is not None:
                altura, largura = img_campo.shape
                img_ref_redimensionada = cv2.resize(img_ref, (largura, altura))
                
                heatmap_campo = cv2.applyColorMap(img_campo, cv2.COLORMAP_INFERNO)
                heatmap_ref = cv2.applyColorMap(img_ref_redimensionada, cv2.COLORMAP_INFERNO)
                
                cv2.putText(heatmap_campo, f"CAMPO: {arq}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(heatmap_campo, f"Brilho: {brilho_campo}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(heatmap_campo, "(Aperte ESPACO p/ prox)", (20, altura - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
                
                cv2.putText(heatmap_ref, f"REFERENCIA: {nome_ref}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(heatmap_ref, f"Brilho: {brilho_ref} | Dif: {diferenca}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                tela_comparacao = np.hstack((heatmap_campo, heatmap_ref))
                cv2.imshow('Comparacao SWIR: Campo vs Referencia', tela_comparacao)
                
                key = cv2.waitKey(0)
                if key == 27:
                    break
            else:
                print(f"Aviso: Não foi possível carregar a imagem de referência visual: {nome_ref}")

    cv2.destroyAllWindows()
    gerar_relatorio(resultados, "relatorio_swir_pasta.xlsx")

def gerar_relatorio(resultados, nome_arquivo):
    if resultados:
        df = pd.DataFrame(resultados)
        df.to_excel(nome_arquivo, index=False)
        print(f"\nSucesso! Planilha '{nome_arquivo}' gerada com {len(resultados)} medições.")
    else:
        print("\nNenhum dado para salvar. Relatório não gerado.")


# MENU INICIAL
if __name__ == '__main__':
    PASTA_REF = "referencia"
    PASTA_COMP = "fotos_comparar"

    print("="*50)
    print(" SISTEMA DE DETECÇÃO DE UMIDADE SWIR ")
    print("="*50)
    print("[1] Usar Câmera Ao Vivo")
    print("[2] Processar Imagens de uma Pasta (com visualização)")
    print("="*50)
    
    escolha = input("Digite o número da opção desejada: ")

    if escolha == '1':
        modo_camera(PASTA_REF, PASTA_COMP)
    elif escolha == '2':
        modo_pasta(PASTA_REF, PASTA_COMP)
    else:
        print("Opção inválida. Execute o script novamente e digite 1 ou 2.")