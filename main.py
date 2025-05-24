import os
import csv
import re
import fitz  # type: ignore
import spacy  # type: ignore

from Models import Paciente

nlp = spacy.load("pt_core_news_sm")


def limpar_texto(texto):
    if not texto:
        return texto
    texto = texto.strip()
    texto = re.sub(r'^[\)\\:\\.\\s]+|[\)\\:\\.\\s]+$', '', texto)
    texto = texto.strip(' .-—–')
    return texto


def extrair_texto_pdf(caminho_pdf):
    try:
        texto = ""
        with fitz.open(caminho_pdf) as pdf:
            for pagina in pdf:
                texto += pagina.get_text()
        return texto
    except Exception:
        return ""


def extrair_datas(texto):
    padrao_data = r'\b(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\b'
    return re.findall(padrao_data, texto)


def extrair_ultimo_desfecho(texto):
    palavras_chave = [
        "alta", "óbito", "obito", "morte", "eutanásia", "eutanasia", "eutanasiado",
        "transferido", "transferência", "internado", "em tratamento", "seguindo tratamento", "veio a óbito"
    ]
    padrao = r'\b(' + '|'.join(palavras_chave) + r')\b'
    ocorrencias = list(re.finditer(padrao, texto.lower()))
    if ocorrencias:
        ultimo = ocorrencias[-1]
        return ultimo.group(1).capitalize()
    return "Não informado"


def extrair_admissao_pdf(arquivos, pasta_pdf):
    for arq in arquivos:
        if isinstance(arq, str) and arq.endswith('.pdf'):
            if any(k in arq.lower() for k in ["admissao", "admissão", "boletim"]):
                caminho_pdf = os.path.join(pasta_pdf, arq)
                if os.path.exists(caminho_pdf):
                    try:
                        texto = extrair_texto_pdf(caminho_pdf)
                        match = re.search(
                            r'(Anamnese.*?admissão[:\-]?\s*)(.+?)(\n\n|\Z)',
                            texto,
                            re.IGNORECASE | re.DOTALL
                        )
                        if match:
                            texto_extraido = match.group(2).strip()
                            texto_extraido = limpar_texto(texto_extraido)
                            return texto_extraido
                    except Exception as e:
                        print(f"Erro lendo {caminho_pdf}: {e}")
    return None


def extrair_exames_por_paciente(arquivos, texto_completo, pasta):
    campos = [
        "Eritrocitos", "Hemoglobina", "Hematocrito", "VCM", "HCM", "CHCM", "RDW",
        "Proteina Total", "Metarrubricito",
        "Leucocitos", "Mielocitos", "Metamielocitos", "Bastonetes", "Segmentados",
        "Eosinofilos", "Basofilos", "Linfocitos", "Linfocitos Atipicos", "Monocitos", "Outros",
        "Contagem Plaquetaria",
        "Creatinina", "Ureia", "ALT", "Fosfatase Alcalina", "Albumina",
        "Colesterol", "Triglicerides", "Glicose", "Fosforo", "Calcio Total"
    ]

   
    nome_paciente = None
    nome_tutor = None
    resenha_match = re.search(r'\*RESENHA\*.*?\*Paciente:\*\s*([^\n*]+).*?\*TUTOR:\*\s*([^\n*]+)', 
                            texto_completo, re.DOTALL | re.IGNORECASE)
    if resenha_match:
        nome_paciente = resenha_match.group(1).strip()
        nome_tutor = resenha_match.group(2).strip()

    def processar_pdf_exame(file_path):
        dados = {campo: 'n/a' for campo in campos}
        
        with fitz.open(file_path) as doc:
            texto = ""
            for page in doc:
                texto += page.get_text()
        
        linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
        
     
        try:
            idx = next(i for i, linha in enumerate(linhas) if "ERITROGRAMA" in linha.upper())
            print(f"\n✅ Seção ERITROGRAMA encontrada na linha {idx}")
            idx += 1
        except StopIteration:
            print("\n⚠ Seção ERITROGRAMA não encontrada")
      
            for alt_section in ["HEMOGRAMA", "EXAME HEMATOLÓGICO", "HEMATO"]:
                try:
                    idx = next(i for i, linha in enumerate(linhas) if alt_section in linha.upper())
                    print(f"\n✅ Seção alternativa {alt_section} encontrada na linha {idx}")
                    idx += 1
                    break
                except StopIteration:
                    continue
            else:
                print("\n❌ Nenhuma seção relevante encontrada")
                return None

        
        mapeamento = {
            "Eritrócitos": "Eritrocitos",
            "Hemoglobina": "Hemoglobina",
            "Hematócrito": "Hematocrito",
            "V.c.m.": "VCM",
            "H.c.m.": "HCM",
            "C.h.c.m.": "CHCM",
            "R.d.w.": "RDW",
            "PROTEÍNA TOTAL": "Proteina Total",
            "METARRUBRÍCITO": "Metarrubricito",
            "Leucócitos": "Leucocitos",
            "Mielócitos": "Mielocitos",
            "Metamielócitos": "Metamielocitos",
            "Bastonetes": "Bastonetes",
            "Segmentados": "Segmentados",
            "Eosinófilos": "Eosinofilos",
            "Basófilos": "Basofilos",
            "Linfócitos": "Linfocitos",
            "Linfócitos atípicos": "Linfocitos Atipicos",
            "Monócitos": "Monocitos",
            "Outros": "Outros",
            "CONTAGEM PLAQUETÁRIA": "Contagem Plaquetaria",
            "Plaquetas": "Contagem Plaquetaria"
        }

  
        for i in range(idx, len(linhas)):
            linha = linhas[i]
            
            for original, padrao in mapeamento.items():
                if original.lower() in linha.lower():
                   
                    for j in range(max(0, i-2), min(len(linhas), i+3)):
                        valor_possivel = linhas[j]
                        if re.search(r'\d', valor_possivel):
                            dados[padrao] = valor_possivel
                            print(f"\n✅ Encontrado {padrao}: {valor_possivel}")
                            break

      
        bioquimicos = {
            "CREATININA": "Creatinina",
            "URÉIA": "Ureia",
            "ALT": "ALT",
            "TGP": "ALT",
            "FOSFATASE ALCALINA": "Fosfatase Alcalina",
            "ALBUMINA": "Albumina",
            "COLESTEROL": "Colesterol",
            "TRIGLICÉRIDES": "Triglicerides",
            "GLICOSE": "Glicose",
            "FÓSFORO": "Fosforo",
            "CÁLCIO TOTAL": "Calcio Total"
        }

        for bio_nome, campo in bioquimicos.items():
            try:
                matches = [i for i, linha in enumerate(linhas) if bio_nome in linha.upper()]
                for match_idx in matches:
                    for i in range(match_idx, min(len(linhas), match_idx + 5)):
                        if re.search(r'\d', linhas[i]):
                            dados[campo] = linhas[i]
                            print(f"\n✅ Encontrado {campo}: {linhas[i]}")
                            break
            except Exception as e:
                print(f"\n⚠ Erro ao processar {campo}: {str(e)}")

        return dados

    arquivos_exame = []
    for arquivo in arquivos:
     
        partes = arquivo.split(';')
        for parte in partes:
          
            parte = re.sub(r'^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}\s+-\s+[^:]+:\s*', '', parte.strip())
            parte = parte.replace('(arquivo anexado)', '').strip()
            
            if parte.endswith('.pdf'):
                
                if nome_paciente and nome_tutor:
                    if (nome_paciente in parte and '(' in parte and ')' in parte and
                        not any(term in parte.lower() for term in 
                            ['admissao', 'admissão', 'evolução', 'evolution', 'boletim'])):
                        print(f"\n🔍 Possível arquivo de exame encontrado: {parte}")
                        arquivos_exame.append(parte)

  
    resultados = []
    for arquivo in arquivos_exame:
        caminho_pdf = os.path.join(pasta, arquivo)
        try:
        
            dados_exame = processar_pdf_exame(caminho_pdf)
            if dados_exame:
                exame_formatado = [f"{campo}: {valor}" for campo, valor in dados_exame.items() if valor != 'n/a']
                if exame_formatado:
                    resultados.extend(exame_formatado)
                    print(f"\n✅ Exame processado com sucesso: {len(exame_formatado)} valores encontrados")
                
        except Exception as e:
            print(f"\n Erro ao processar {arquivo}: {str(e)}")

    return resultados


def parse_patient_data(file_content, pasta_pdf):
    patient_data = {}
    arquivos = []

    grupo_match = re.search(r'criou o grupo\s+".+\s+\((\d+)\)"', file_content)
    if grupo_match:
        patient_data['codigo'] = grupo_match.group(1).strip()

    current_section = None

    for line in file_content.split('\n'):
        line = line.strip()

        if "<Mídia oculta>" in line or "(arquivo anexado)" in line or ".pdf" in line.lower():
            if ".pdf" in line.lower():
                arquivos.append(line.strip())
            else:
                arquivo_limpo = re.sub(r'^.*? - .*?:\s*', '', line)
                arquivo_limpo = arquivo_limpo.replace("(arquivo anexado)", "").strip()
                arquivos.append(arquivo_limpo)
            continue

        if "*RESENHA*" in line:
            current_section = "RESENHA"
            continue

        if current_section == "RESENHA":
            if "*Peso:*" in line:
                patient_data["peso"] = limpar_texto(line.split("*Peso:*")[1].strip())
            elif "*CÓDIGO:*" in line:
                patient_data["codigo"] = limpar_texto(line.split("*CÓDIGO:*")[1].strip())
            elif "*Espécie:*" in line:
                patient_data["especie"] = limpar_texto(line.split("*Espécie:*")[1].strip())
            elif "*Raça:*" in line:
                patient_data["raca"] = limpar_texto(line.split("*Raça:*")[1].strip())
            elif "*Idade:*" in line:
                patient_data["idade"] = limpar_texto(line.split("*Idade:*")[1].strip())
            elif "*Motivo da internação:*" in line:
                patient_data["motivo"] = limpar_texto(line.split("*Motivo da internação:*")[1].strip())

    doc = nlp(file_content)

    if not patient_data.get("cirurgia"):
        cirurgia_match = re.search(
            r'\b(cirurgia|cirúrgico|procedimento cirúrgico|operação|operar)\b',
            file_content.lower()
        )
        patient_data["cirurgia"] = 1 if cirurgia_match else 0

    if not patient_data.get("idade"):
        idade_match = re.search(r'(\d{1,2})\s*(anos|ano|meses|mês)', file_content.lower())
        if idade_match:
            patient_data["idade"] = limpar_texto(idade_match.group(0).strip())

    if not patient_data.get("peso"):
        peso_match = re.search(r'Peso:?\s*([\d.,]+)', file_content)
        if peso_match:
            patient_data["peso"] = limpar_texto(peso_match.group(1).replace(',', '.'))

    if not patient_data.get("especie"):
        especie_match = re.search(r'\b(cão|cachorro|gato|felino|canino|canina|felina)\b', file_content.lower())
        if especie_match:
            especie = especie_match.group(0).capitalize()
            patient_data["especie"] = especie if especie not in ['Cachorro', 'Cão'] else 'Canina'

    if not patient_data.get("raca"):
        raca_match = re.search(r'Raça:?\s*(.*?)(\n|Sexo:)', file_content, re.IGNORECASE)
        if raca_match:
            raca_val = limpar_texto(raca_match.group(1).strip())
            if raca_val.lower() not in ["sexo", "responsável", "proprietário", ""] and len(raca_val) > 1:
                patient_data["raca"] = raca_val

    if not patient_data.get("desfecho"):
        patient_data["desfecho"] = extrair_ultimo_desfecho(file_content)

    admissao_texto = extrair_admissao_pdf(arquivos, pasta_pdf)
    if admissao_texto:
        patient_data["admissao"] = admissao_texto
    else:
        patient_data["admissao"] = "Não informado"

    alimentacao = [
        sent.text.strip()
        for sent in doc.sents
        if re.search(r'\balimentação\b|\bdieta\b|\bcomida\b', sent.text.lower())
    ]
    patient_data["alimentacao"] = alimentacao if alimentacao else None

    patient_data["arquivos"] = arquivos

    clinico = extrair_exames_por_paciente(arquivos, file_content, pasta_pdf)
    patient_data["clinico"] = clinico if clinico else []

    return patient_data


def process_files(folder_path):
    pacientes = {}
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt') and re.search(r'\d+', filename):
            with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as f:
                content = f.read()
                data = parse_patient_data(content, folder_path)
                codigo = data.get("codigo")
                if not codigo:
                    file_code_match = re.search(r'(\d+)', filename)
                    if file_code_match:
                        codigo = file_code_match.group(1)
                        data["codigo"] = codigo
                    else:
                        continue
                pacientes[codigo] = Paciente(**data)
    return pacientes


def save_to_csv(pacientes, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["codigo", "peso", "especie", "raca", "idade", "motivo", "admissao", "cirurgia",
                      "alimentacao", "arquivos", "desfecho", "clinico"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for codigo, paciente in pacientes.items():
            writer.writerow({
                "codigo": paciente.codigo,
                "peso": paciente.peso,
                "especie": paciente.especie,
                "raca": paciente.raca,
                "idade": paciente.idade,
                "motivo": paciente.motivo,
                "admissao": paciente.admissao,
                "cirurgia": "Sim" if paciente.cirurgia else "Não",
                "alimentacao": "; ".join(paciente.alimentacao) if paciente.alimentacao else "",
                "arquivos": "; ".join(paciente.arquivos) if paciente.arquivos else "",
                "desfecho": paciente.desfecho,
                "clinico": "; ".join(paciente.clinico) if paciente.clinico else ""
            })


if __name__ == "__main__":
    folder_path = "HACKATHON/HACKATHON"
    output_csv = "pacientes.csv"

    pacientes = process_files(folder_path)
    save_to_csv(pacientes, output_csv)

