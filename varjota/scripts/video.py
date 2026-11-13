"""Gera o vídeo narrado do estudo de Varjota.

Uso: python3 video.py <modelo_piper.onnx> <pasta_trabalho>
Requer: piper-tts, num2words, Pillow, ffmpeg.
"""
import re, subprocess, sys, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from num2words import num2words

MODEL, WORK = sys.argv[1], Path(sys.argv[2]); WORK.mkdir(parents=True, exist_ok=True)
BASE = Path(__file__).resolve().parent.parent
G = BASE / "graficos"
W, H = 1920, 1080
FONT = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
NAVY, ORANGE, INK, MUTED, BG = "#13233d", "#E8A33D", "#1d2330", "#5b6372", "#f6f4ef"
RED, BLUE = "#C0392B", "#2F6DB5"


def f(w, s): return ImageFont.truetype(FONT.format(w), s)


def wrap(d, text, font, maxw):
    out = []
    for para in text.split("\n"):
        line = ""
        for w_ in para.split():
            t = (line + " " + w_).strip()
            if d.textlength(t, font=font) <= maxw: line = t
            else: out.append(line); line = w_
        out.append(line)
    return out


def card(name, kicker, title, bullets=(), big=None, note=None, dark=False):
    bg, fg, mu = (NAVY, "white", "#b9c3d6") if dark else (BG, INK, MUTED)
    im = Image.new("RGB", (W, H), bg); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 24, H], fill=ORANGE)
    y = 110
    if kicker:
        d.text((130, y), kicker.upper(), font=f("SemiBold", 34), fill=ORANGE); y += 70
    for ln in wrap(d, title, f("Bold", 76), W - 260):
        d.text((130, y), ln, font=f("Bold", 76), fill=fg); y += 92
    y += 30
    if big:
        d.text((130, y), big, font=f("Bold", 170), fill=ORANGE); y += 220
    for b in bullets:
        col = fg
        if isinstance(b, tuple): b, col = b
        lines = wrap(d, b, f("Medium", 44), W - 330)
        d.ellipse([140, y + 20, 156, y + 36], fill=ORANGE)
        for ln in lines:
            d.text((190, y), ln, font=f("Medium", 44), fill=col); y += 58
        y += 22
    if note:
        d.text((130, H - 110), note, font=f("Regular", 30), fill=mu)
    p = WORK / f"{name}.png"; im.save(p); return p


def table(name, kicker, title, header, rows, note=None, widths=None):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 24, H], fill=ORANGE)
    d.text((130, 110), kicker.upper(), font=f("SemiBold", 34), fill=ORANGE)
    d.text((130, 180), title, font=f("Bold", 70), fill=INK)
    n = len(header); x0, x1 = 130, W - 130; y = 330
    widths = widths or [1 / n] * n
    xs = [x0 + sum(widths[:i]) * (x1 - x0) for i in range(n)]
    d.rectangle([x0, y, x1, y + 80], fill=NAVY)
    for i, h in enumerate(header):
        d.text((xs[i] + 20, y + 18), h, font=f("SemiBold", 38), fill="white")
    y += 80
    for r_i, r in enumerate(rows):
        hl = isinstance(r, tuple) and len(r) == 2 and isinstance(r[1], bool)
        cells = r[0] if hl else r
        d.rectangle([x0, y, x1, y + 84], fill="#fff4dd" if hl else ("white" if r_i % 2 == 0 else "#eeeae2"))
        for i, c in enumerate(cells):
            d.text((xs[i] + 20, y + 20), str(c), font=f("Bold" if hl or i == 0 else "Medium", 40), fill=INK)
        y += 84
    if note:
        for k, ln in enumerate(wrap(d, note, f("Regular", 34), W - 260)):
            d.text((130, y + 40 + k * 46), ln, font=f("Regular", 34), fill=MUTED)
    p = WORK / f"{name}.png"; im.save(p); return p


# ---------------------------------------------------------------- texto falado
SIGLAS = {"PSB": "pê-ésse-bê", "MDB": "ême-dê-bê", "PDT": "pê-dê-tê", "PT": "pê-tê", "PL": "pê-éle", "PP": "pê-pê",
          "PCdoB": "pê-cê do bê", "PV": "pê-vê", "PSDB": "pê-ésse-dê-bê", "PTB": "pê-tê-bê", "PSL": "pê-ésse-éle",
          "TSE": "tê-ésse-é", "CRAS": "cras", "QE": "quociente eleitoral"}


def falar(t):
    for k, v in SIGLAS.items(): t = re.sub(rf"\b{k}\b", v, t)
    t = re.sub(r"(\d+),(\d+)\s?%", lambda m: f"{num2words(int(m[1]), lang='pt_BR')} vírgula {num2words(int(m[2]), lang='pt_BR')} por cento", t)
    t = re.sub(r"(\d+)\s?%", lambda m: f"{num2words(int(m[1]), lang='pt_BR')} por cento", t)
    t = re.sub(r"\d{1,3}(?:\.\d{3})+", lambda m: num2words(int(m[0].replace(".", "")), lang="pt_BR"), t)
    t = re.sub(r"(\d+),(\d+)", lambda m: f"{num2words(int(m[1]), lang='pt_BR')} vírgula {num2words(int(m[2]), lang='pt_BR')}", t)
    t = re.sub(r"\d+", lambda m: num2words(int(m[0]), lang="pt_BR"), t)
    return t.replace("×", " a ").replace("→", " para ")


# ---------------------------------------------------------------- roteiro
S = []
def cena(img, texto): S.append((img, texto))

cena(card("00", "Estudo político-eleitoral", "Varjota, Ceará: o que os números contam de 2020 a 2026, e o que esperar de 2028",
          ["Prefeito, Câmara, quociente eleitoral e sobras", "Migrações, geografia do voto e entrelinhas", "Projeção para 2028"],
          note="Fonte: dados abertos do TSE · município 98574 · 65ª Zona Eleitoral", dark=True),
     "Este é um estudo político-eleitoral de Varjota, no Ceará. Vamos olhar as eleições municipais de 2020 e 2024, "
     "as eleições gerais de 2022 e 2026, e terminar com uma projeção para 2028. Todos os números vêm dos dados abertos do TSE. "
     "Quando algo for interpretação, e não número, eu vou avisar.")

cena(card("01", "Resumo", "Cinco ideias para guardar",
          ["Elmo Monte foi de 53,1% em 2020 para 64,3% em 2024",
           "A Câmara virou: oposição tinha 6 de 11 cadeiras; hoje tem 3",
           "Quociente eleitoral subiu de 1.199 para 1.252 votos",
           "Em 2026, Varjota deu 58% a Ciro Gomes para governador",
           "2028 é sucessão aberta: Elmo não pode concorrer"]),
     "Se você guardar só cinco coisas, guarde estas. Primeiro: o prefeito Elmo Monte saiu de uma vitória apertada, com 53,1%, "
     "para uma vitória larga, com 64,3%. Segundo: a Câmara virou. Em 2020 a oposição tinha seis das onze cadeiras, e hoje tem três. "
     "Terceiro: o quociente eleitoral subiu de 1.199 para 1.252 votos. Quarto: em 2026, Varjota votou em Ciro Gomes para governador, "
     "contrariando o resultado estadual. E quinto: 2028 será uma sucessão aberta, porque Elmo já está no segundo mandato.")

cena(card("02", "Parte 1", "Quem vota em Varjota", dark=True), "Parte um. Quem vota em Varjota.")
cena(G / "02_comparecimento.png",
     "O cadastro está encolhendo. Eram 16.757 eleitores em 2022, 16.213 em 2024 e 15.991 em 2026. "
     "Mas repare no comparecimento. Na eleição municipal de 2024, 88,7% dos eleitores foram votar. Na eleição geral de 2022, só 76,7%. "
     "Em Varjota, a eleição que mobiliza é a da prefeitura. E em 2024 a abstenção caiu em 872 pessoas, mesmo com menos eleitores aptos.")
cena(G / "08_eleitorado.png",
     "O perfil também mudou. A faixa de 16 a 24 anos perdeu 256 eleitores, enquanto a faixa de 45 a 59 anos ganhou 280. "
     "Analfabetos caíram de 10% para 7,2% do eleitorado. Mas mais da metade ainda não concluiu o ensino fundamental. "
     "Isso indica que comunicação de proximidade, como visita, áudio e liderança comunitária, pesa mais que debate de programa.")

cena(card("03", "Parte 2", "A disputa pela prefeitura", dark=True), "Parte dois. A disputa pela prefeitura.")
cena(G / "01_prefeito.png",
     "Em 2020, Elmo Monte, então no PDT, venceu Rosa Paulino, do MDB, por 7.068 a 6.238 votos. Diferença de 830 votos. "
     "Em 2024, já no PSB, Elmo fez 8.914 votos contra 4.955 de Silvino Oliveira, do MDB. A diferença saltou para 3.959 votos. "
     "Ele ganhou 1.846 votos novos, e a oposição perdeu 1.283.")
cena(card("04", "Entrelinhas", "Trocou de partido e de vice, e cresceu",
          ["2020: Elmo (PDT) + vice Loura do Povo (PDT)",
           ("2024: Loura do Povo vira vice da OPOSIÇÃO, pelo PP", BLUE),
           ("2024: Elmo (PSB) + vice Dr. Erivaldo Mororó (Republicanos)", RED),
           "Coligação cresce: entram Republicanos e União",
           "Oposição encolhe: perde o PL, fica só PP + MDB"]),
     "Aqui está a primeira entrelinha. A vice eleita em 2020, Loura do Povo, rompeu com o grupo e foi ser vice na chapa adversária, pelo PP. "
     "Normalmente isso enfraquece o prefeito. Mas aconteceu o contrário. Elmo trocou o PDT pelo PSB, acompanhando o movimento estadual do seu grupo, "
     "trouxe Republicanos e União para a coligação, e escolheu um médico como vice. A oposição perdeu o PL e ficou só com PP e MDB.")
cena(G / "06_geografia.png",
     "Este gráfico mostra cada local de votação. No eixo horizontal, o percentual de Elmo em 2020. No vertical, o de 2024. "
     "Todos os pontos estão acima da diagonal, ou seja, Elmo cresceu em todos os locais. Em 2020 a oposição venceu em sete locais. Em 2024, em nenhum. "
     "As maiores viradas aconteceram na zona rural: no Sítio Jatobá, quase 30 pontos, e no Sítio Angelim, 24 pontos.")
cena(card("05", "Entrelinhas", "Onde a oposição ainda resiste",
          ["Melquíades Muniz Farrapo (Transval, rural): só +4,3 pontos",
           "Vicente Trajano de Mesquita (Olho d'Água dos Trajano): +4,5",
           "Francisco Pereira da Costa: +5,6",
           "Liceu Waldir Leopércio, 2º maior local da cidade: +6,2",
           "Centro Digital: +7,1"], note="Variação do % de Elmo entre 2020 e 2024 por local de votação"),
     "E onde a oposição resistiu? Nos locais em que Elmo menos cresceu: Transval, Olho d'Água dos Trajano, Francisco Pereira da Costa, "
     "o Liceu, que é o segundo maior local da cidade, e o Centro Digital. Para quem pensa 2028, é por esses locais que uma oposição deveria começar, "
     "e é neles que a base precisa reforçar a presença.")

cena(card("06", "Parte 3", "A Câmara: quociente, sobras e cadeiras", dark=True), "Parte três. A Câmara Municipal. Aqui está a matemática que decide quem entra.")
cena(card("07", "Como funciona", "A conta do quociente eleitoral",
          ["Quociente eleitoral = votos válidos ÷ 11 cadeiras",
           "Quociente partidário = votos do partido ÷ quociente eleitoral (sem a fração)",
           "Sobras: maior média = votos do partido ÷ (cadeiras + 1)",
           "Para disputar sobra: partido com pelo menos 80% do QE",
           "Para ser eleito: candidato com pelo menos 10% do QE"]),
     "Antes dos números, a regra. O quociente eleitoral é o total de votos válidos para vereador dividido por onze cadeiras. "
     "Cada partido ganha uma cadeira para cada quociente que alcança. As cadeiras que sobram vão para quem tiver a maior média, "
     "que é o total de votos do partido dividido pelas cadeiras que já tem mais um. Para disputar essas sobras, o partido precisa de pelo menos 80% do quociente. "
     "E o candidato precisa ter pelo menos 10% do quociente para ser eleito.")
cena(G / "03_quociente_2020.png",
     "Em 2020 foram 13.184 votos válidos. O quociente ficou em 1.199. O MDB fez 5.348 votos e cinco cadeiras. O PDT, 4.066 votos e quatro cadeiras. "
     "PT e PL fizeram uma cada. A última cadeira ficou com o PDT, mas o PT ficou a apenas 90 votos de tomá-la. "
     "Resultado: a oposição, MDB e PL, ficou com seis cadeiras, e a base do prefeito com cinco.")
cena(G / "03_quociente_2024.png",
     "Em 2024 foram 13.768 votos válidos e o quociente subiu para 1.252. Só três listas disputaram. O PSB fez 6.403 votos e cinco cadeiras. "
     "O MDB, 3.979 e três cadeiras. A federação do PT, 3.386 votos, duas cadeiras pelo quociente e mais uma na sobra. "
     "Na disputa pela sobra, a federação teve média de 1.128, contra 1.067 do PSB. Faltaram 371 votos para o PSB fazer a sexta cadeira.")
cena(table("08", "Votos por cadeira em 2024", "Quanto custou cada cadeira",
           ["Lista", "Votos", "Cadeiras", "Votos/cadeira"],
           [["PSB", "6.403", "5", "1.281"], ["MDB", "3.979", "3", "1.326"], ["Fed. PT/PCdoB/PV", "3.386", "3", "1.129"]],
           note="A cadeira mais barata foi a da federação do PT. Com 371 votos a mais, o PSB teria feito 6 cadeiras."),
     "Olhe quanto custou cada cadeira. Para o MDB, 1.326 votos. Para o PSB, 1.281. Para a federação do PT, só 1.129. "
     "Se a base tivesse distribuído melhor os candidatos entre PSB e PT, poderia ter feito uma cadeira a mais. Essa é uma lição prática para 2028.")
cena(G / "04_camara.png",
     "O resultado político é este. Em 2020, a base do prefeito tinha cinco vereadores e a oposição seis. Em 2024, a base tem oito e a oposição três. "
     "Uma supermaioria governista.")
cena(G / "05_vereadores_2024.png",
     "Agora os nomes. A vereadora mais votada de 2024 foi Rosa Paulino, do MDB, com 1.774 votos, quase o dobro do segundo colocado, Eudes Mesquita, do PSB, com 992. "
     "Repare em Eudes do Croatá, do MDB, eleito com 280 votos, enquanto Aristeu Linhares, do PSB, ficou de fora com 553. "
     "Isso é o efeito lista: o voto do partido decide, e não só o voto do candidato.")
cena(card("09", "Renovação", "7 dos 11 vereadores são novos",
          ["6 eleitos de 2020 tentaram de novo; 4 se reelegeram",
           "Não concorreram: Antunino, Molim, Jô do Silvino, Marcos Cesar (MDB) e Edgar Procópio (PL)",
           "Os 5 eram da oposição e somavam 3.311 votos",
           "Mulheres eleitas: de 2 para 5",
           "Candidatos: de 48 para 34 · com menos de 100 votos: de 19 para 8"]),
     "Houve uma renovação grande. Sete dos onze vereadores atuais são novos. Dos eleitos em 2020, cinco nem tentaram a reeleição, "
     "e todos os cinco eram da oposição. Juntos, eles tinham feito 3.311 votos. A oposição perdeu os seus puxadores de voto. "
     "Outro dado: as mulheres na Câmara passaram de duas para cinco. E o número de candidatos caiu de 48 para 34, com muito menos candidatos de pouquíssimos votos.")

cena(card("10", "Parte 4", "Quem foi para onde", dark=True), "Parte quatro. As migrações partidárias.")
cena(G / "07_migracoes.png",
     "Cruzando o título de eleitor dos candidatos, dá para ver quem trocou de partido. A bancada do PDT foi inteira para o PSB, junto com o prefeito. "
     "O vereador Anchieta saiu do MDB e foi para o PSB, mas não se reelegeu. Suplentes do MDB, como Lyderson, Pexé e Carlim, também aderiram à base. "
     "O PL local se desfez: Adriano Paiva e Irmã Moça foram para o MDB, e Irmã Fábia para o PT. O fluxo foi quase todo da oposição para o governo, "
     "e a única grande saída da base foi a da vice.")

cena(card("11", "Parte 5", "Varjota nas eleições gerais", dark=True), "Parte cinco. Como Varjota vota nas eleições gerais.")
cena(G / "09_2022.png",
     "Em 2022, Varjota deu 72,3% a Lula no segundo turno. Para governador, Elmano, do PT, teve 45,5%, Roberto Cláudio, do PDT, 31,6%, e Capitão Wagner, 22,8%. "
     "Para deputado estadual, Lia Gomes teve 34% e Danniel Oliveira, do MDB, 22%. São os dois blocos locais aparecendo no voto para a Assembleia.")
cena(G / "09b_2026.png",
     "Em 2026, uma surpresa. Ciro Gomes, pelo PSDB, venceu em Varjota com 58,1%, contra 41,6% de Elmano, que foi reeleito no estado. "
     "Para o Senado, o voto se dividiu quase igual entre quatro nomes, com Capitão Wagner à frente e Cid Gomes em segundo. "
     "Lula caiu para 66,5% no segundo turno. Para deputado estadual, Lia Gomes e Danniel Oliveira repetiram praticamente os mesmos percentuais de 2022.")
cena(card("12", "Entrelinhas de 2026", "O voto local não se transfere automaticamente",
          ["Lia Gomes (30%) × Danniel Oliveira (22%): blocos locais estáveis",
           "Dep. federal: MDB concentra (Yury 19%); base pulveriza (PSB ≈ 33% em 4 nomes)",
           "Governador: Ciro 58% apesar da base local ser aliada do PT",
           "Lula perde cerca de 6 pontos: abre espaço para lista de direita em 2028"]),
     "O que isso diz nas entrelinhas? Primeiro: os dois blocos locais são estáveis. Segundo: na eleição para deputado federal, a oposição concentra o voto em um nome, "
     "e a base divide entre vários aliados. Terceiro: a máquina local transfere pouco voto em eleição estadual. Ciro venceu mesmo com a base local aliada ao PT. "
     "Isso pode ser voto pessoal de Ciro na região de Sobral, ou parte da base apoiando Ciro. É uma hipótese a confirmar em campo, e pode reorganizar as alianças de 2028. "
     "E quarto: a queda de Lula abre espaço para uma lista de direita na Câmara, que em 2024 não existiu.")

cena(card("13", "Parte 6", "As entrelinhas", dark=True), "Parte seis. As entrelinhas que não aparecem na manchete.")
cena(card("14", "Entrelinhas", "O que está por trás dos números (1/2)",
          ["A oposição tinha maioria em 2020 e não conseguiu manter",
           "Rosa Paulino fez 45% de todos os votos do MDB para vereador",
           "Se Rosa disputar a prefeitura, o MDB perde cerca de 1.800 votos na lista",
           "Voto de legenda caiu de 608 para 343: o eleitor vota em pessoa",
           "Apelidos de urna mostram as bases familiares e comunitárias"]),
     "A oposição venceu a Câmara em 2020 e não conseguiu manter essa força. Hoje ela depende de uma pessoa: Rosa Paulino fez 45% de todos os votos do MDB para vereador. "
     "Se Rosa for candidata a prefeita em 2028, a lista do MDB perde cerca de 1.800 votos, o que pode custar uma ou duas cadeiras. "
     "O voto de legenda caiu de 608 para 343: em Varjota, o eleitor vota em pessoa, não em partido. E os apelidos de urna, como do Garrone, do Silvino, do Croatá e da Célia, "
     "mostram que as bases são familiares e comunitárias.")
cena(card("15", "Entrelinhas", "O que está por trás dos números (2/2)",
          ["Cadeiras decididas por 90 votos (2020) e 371 votos (2024)",
           "Abstenção caiu quando a eleição ficou desequilibrada: mobilização organizada",
           "Locais ligados a CRAS, Secretaria e creches avançaram 17 pontos ou mais",
           "A zona rural decide: maiores viradas e maiores resistências",
           "Novo vice sem voto testado nas urnas: sucessor natural, mas não automático"]),
     "Mais entrelinhas. As últimas cadeiras foram decididas por 90 votos em 2020 e 371 em 2024. Ou seja, uma seção eleitoral pode mudar a Câmara. "
     "A abstenção caiu justamente quando a eleição ficou desequilibrada, o que indica mobilização organizada, e não entusiasmo espontâneo. "
     "Os locais ligados a equipamentos sociais avançaram 17 pontos ou mais. A zona rural concentrou tanto as maiores viradas quanto as maiores resistências. "
     "E o vice atual é sucessor natural, mas não tem voto próprio testado nas urnas.")

cena(card("16", "Parte 7", "Projeção para 2028", dark=True), "Parte sete. A projeção para 2028.")
cena(table("17", "Premissas", "Quociente eleitoral projetado",
           ["Cenário", "Aptos", "Válidos", "QE", "80% QE"],
           [["Baixo", "15.600", "12.778", "1.162", "930"], (["Central", "15.850", "13.286", "1.208", "967"], True),
            ["Alto", "16.100", "13.727", "1.248", "999"]],
           note="Comparecimento de 85,5% / 87,5% / 89%; válidos = 95,8% do comparecimento; 11 cadeiras; até 12 candidatos por partido."),
     "Considerando que o eleitorado continua encolhendo, projetamos entre 15.600 e 16.100 eleitores aptos em 2028. No cenário central, "
     "com 87,5% de comparecimento, teremos cerca de 13.300 votos válidos para vereador, e um quociente eleitoral de aproximadamente 1.208 votos. "
     "Para disputar as sobras, um partido vai precisar de cerca de 970 votos. A faixa provável do quociente vai de 1.162 a 1.248.")
cena(G / "10_projecao_qe.png",
     "Comparando: 1.199 em 2020, 1.252 em 2024, e algo entre 1.160 e 1.250 em 2028. Cada partido pode lançar até doze candidatos. "
     "Com uma sucessão aberta, a tendência é aparecerem mais listas, entre três e cinco, com algo entre 33 e 55 candidatos a vereador.")
cena(table("18", "Simulação", "Como pode ficar a Câmara em 2028",
           ["Cenário", "Divisão dos votos", "Cadeiras"],
           [["A · continuidade", "PSB 45 · PT 25 · MDB 30", "5 · 3 · 3"],
            ["B · fragmentação", "PSB 33 · PT 20 · MDB 25 · Rep 12 · PL 10", "4 · 2 · 3 · 1 · 1"],
            ["C · oposição cresce", "PSB 36 · PT 20 · MDB 38 · PP 6", "4 · 2 · 5 · 0"]],
           widths=[.25, .52, .23], note="Quociente central de 1.208. No cenário C, o PP com 6% não alcança 80% do QE e fica sem cadeira."),
     "Simulamos três cenários. No primeiro, de continuidade, a Câmara repete 2024: oito a três para a base. No segundo, de fragmentação, "
     "os aliados lançam listas próprias e a Câmara fica com cinco partidos, mas a base mantém a maioria. No terceiro, se a oposição crescer e o MDB chegar a 38% dos votos, "
     "ele faz cinco cadeiras e o placar fica seis a cinco. Note que um partido com só 6% não chega à barreira e fica de fora.")
cena(card("19", "Prefeito 2028", "Três caminhos para a sucessão",
          [("Continuidade unida: um nome da base, coligação de 2024 mantida, base com 55–62%", RED),
           "Base dividida: PT ou Republicanos com candidato próprio; disputa aberta",
           ("Oposição unificada: MDB, com Rosa Paulino ou nome novo, + PP/PL, oposição com 42–50%", BLUE)],
          note="Elmo Monte não pode concorrer (2º mandato consecutivo)."),
     "Para prefeito, vemos três caminhos. Se a base se mantiver unida em torno de um nome, ela parte na frente, com algo entre 55 e 62%. "
     "Se a base se dividir, com PT ou Republicanos lançando candidato próprio, a disputa fica aberta. E se a oposição se unificar, "
     "com Rosa Paulino ou um nome novo, somando PP e PL, e aproveitando o desgaste de oito anos de governo, ela pode chegar entre 42 e 50%.")
cena(card("20", "O que observar", "Variáveis-chave até 2028",
          ["Quem será o sucessor indicado, e se a base aceita",
           "Rosa Paulino: prefeitura ou Câmara?",
           "Rearranjo estadual: Ciro × PSB de Cid × PT de Elmano",
           "Comunidades rurais de baixo avanço e o Liceu",
           "Republicanos e União: lista própria ou aliança?",
           "Eleitorado jovem, que vem caindo"]),
     "Até 2028, fique de olho em seis coisas. Quem será o sucessor indicado pelo prefeito, e se a base aceita esse nome. Se Rosa Paulino vai disputar a prefeitura ou ficar na Câmara. "
     "Como o rearranjo estadual entre Ciro, o PSB de Cid e o PT de Elmano vai chegar a Varjota. O comportamento das comunidades rurais de baixo avanço e do Liceu. "
     "Se Republicanos e União vão lançar lista própria. E a evolução do eleitorado jovem.")
cena(card("21", "Encerramento", "Os números mostram a força. As entrelinhas mostram onde ela é frágil.",
          ["Estudo completo, tabelas e script: pasta varjota/ do repositório",
           "Fonte: TSE, dados abertos (2020, 2022, 2024 e 2026)"], dark=True),
     "Resumindo: os números mostram um grupo governista muito forte em 2024. As entrelinhas mostram onde essa força é frágil: "
     "dependência da máquina, voto local que não se transfere para cima, e uma sucessão sem nome natural. "
     "O estudo completo, com todas as tabelas e o script para refazer as contas, está na pasta varjota do repositório. Obrigado.")

# ---------------------------------------------------------------- render
clips = []; srt = []; t0 = 0.0
for i, (img, txt) in enumerate(S):
    wav = WORK / f"n{i:02d}.wav"
    if not wav.exists():
        subprocess.run([sys.executable, "-m", "piper", "-m", MODEL, "-f", str(wav), "--length-scale", "1.05", "--sentence-silence", "0.35"],
                       input=falar(txt).encode(), check=True, capture_output=True)
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)]))
    tot = dur + 1.0
    mp4 = WORK / f"c{i:02d}.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "30", "-i", str(img), "-i", str(wav),
                    "-filter_complex", f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=white,"
                    f"fade=t=in:st=0:d=0.4,fade=t=out:st={tot-0.4:.2f}:d=0.4,format=yuv420p[v];[1:a]adelay=400|400,apad[a]",
                    "-map", "[v]", "-map", "[a]", "-t", f"{tot:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                    "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "1", str(mp4)], check=True)
    clips.append(mp4)
    def ts(s): return f"{int(s//3600):02d}:{int(s%3600//60):02d}:{int(s%60):02d},{int((s%1)*1000):03d}"
    srt.append(f"{i+1}\n{ts(t0+0.4)} --> {ts(t0+tot)}\n{txt}\n")
    t0 += tot
    print(f"cena {i:02d}: {tot:.1f}s", flush=True)
(WORK / "lista.txt").write_text("".join(f"file '{c}'\n" for c in clips))
out = BASE / "video" / "varjota_estudo_2020-2028.mp4"; out.parent.mkdir(exist_ok=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(WORK / "lista.txt"), "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
(BASE / "video" / "varjota_estudo_2020-2028.srt").write_text("\n".join(srt))
(BASE / "video" / "roteiro.md").write_text("# Roteiro do vídeo\n\n" + "\n\n".join(f"**Cena {i+1}**\n\n{t}" for i, (_, t) in enumerate(S)))
print("OK", out, f"{t0/60:.1f} min")
