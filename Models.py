class Paciente:
    def __init__(self, **kwargs):
        self.codigo = kwargs.get("codigo", "")
        self.peso = kwargs.get("peso", "Não Informado")
        self.especie = kwargs.get("especie", "")
        self.raca = kwargs.get("raca", "")
        self.idade = kwargs.get("idade", "")
        self.motivo = kwargs.get("motivo", "N/A")
        self.admissao = kwargs.get("admissao", "Não informado")
        self.cirurgia = kwargs.get("cirurgia", 0)
        self.desfecho = kwargs.get("desfecho", "Não informado")
        self.clinico = kwargs.get("clinico", [])  
        self.alimentacao = kwargs.get("alimentacao", [])
        self.arquivos = kwargs.get("arquivos", [])
