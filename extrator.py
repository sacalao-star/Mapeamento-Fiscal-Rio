# ============================================================
# MÓDULO DE INTELIGÊNCIA E EXTRAÇÃO AUTOMATIZADA - PRISMA RIO
# ============================================================
import requests
import json
import urllib.parse
import os

def geocodificar_endereco(endereco_completo):
    """
    Usa a API pública do OpenStreetMap (Nominatim) para converter 
    um endereço escrito (ex: Rua da Regeneração) em Latitude e Longitude reais.
    """
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(endereco_completo)}&format=json&limit=1"
    headers = {'User-Agent': 'PrismaRioAutomationBot/2.0'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"Erro na geocodificação: {e}")
        
    return None, None

def minerar_novos_ativos():
    """
    Simula a varredura inteligente de editais e diários oficiais da PGM/RJ 
    em busca de novos galpões e terrenos endividados.
    """
    print("🔍 Iniciando varredura automatizada em fontes públicas e editais...")
    
    # Exemplo de alvos minerados de fontes de execuções fiscais recentes
    novos_alvos = [
        {
            "id": "SQL-887.412-9",
            "endereco": "Rua Uranos, Bonsucesso",
            "bairro": "Bonsucesso",
            "area_m2": 6200,
            "valor_aproximado": 11000000,
            "status": "Execução Fiscal PGM",
            "trilha": "Varejo e Logística",
            "detalhes": "Galpão industrial autuado recentemente por abandono e débitos de IPTU na região norte."
        },
        {
            "id": "SQL-776.321-4",
            "endereco": "Avenida Brasil, Ramos",
            "bairro": "Ramos",
            "area_m2": 18000,
            "valor_aproximado": 42000000,
            "status": "Dívida Ativa / Leilão",
            "trilha": "Varejo e Logística",
            "detalhes": "Complexo de armazéns à margem da Av. Brasil com processo de penhora ativo."
        }
    ]
    
    ativos_validados = []
    for item in novos_alvos:
        print(f"📍 Georreferenciando: {item['endereco']}...")
        lat, lon = geocodificar_endereco(item['endereco'] + ", Rio de Janeiro, Brasil")
        
        if lat and lon:
            item['lat'] = lat
            item['lon'] = lon
            ativos_validados.append(item)
            print(f"   Sucesso! Coordenadas obtidas: Lat {lat}, Lon {lon}")
        else:
            print("   ⚠️ Endereço não validado.")
            
    return ativos_validados

if __name__ == "__main__":
    resultado = minerar_novos_ativos()
    print(f"\n✨ Automação finalizada com sucesso! {len(resultado)} novos ativos processados.")
