# Nexus Core v0.8.0 — Device Registry Foundation

## Entregas implementadas na branch de desenvolvimento

- Fundação `nexus.devices` para **declarações explícitas e locais** de nós Arduino e ESP32.
- Contrato `nexus.devices.v1` com lista limitada a 32 dispositivos; identificadores únicos, rótulos, família e apenas capacidades de **leitura** declarativas.
- Validação estrita de JSON: tamanho máximo de 16 KiB, rejeição de campos imprevistos, chaves duplicadas, repetição de IDs, tipos inválidos, comandos, URLs, segredos e transportes não desabilitados.
- Registro atômico **em memória**, com listagem determinística e exclusão explícita; nenhum dispositivo é automaticamente descoberto, pareado, salvo, ligado ou acionado.
- `nexus-core --devices-check`: relatório passivo sobre a capacidade de leitura de manifestos, sem banco, USB, serial, Bluetooth ou rede.
- `nexus-core --devices-preview-stdin`: valida o JSON recebido pelo stdin e imprime somente um resumo limitado dos dispositivos declarados. Não estabelece conexão.
- Testes de unidades, entrada hostil, CLI sem inicialização da aplicação, status e integração com `NexusApplication`.
- Sem alterações de aparência na GUI, voz, visão, PostgreSQL, Ollama nem na segurança dos comandos X11 da v0.7.3.

### Manifesto válido para prévia (sem conectar o sensor)

```json
{
  "schema": "nexus.devices.v1",
  "devices": [
    {
      "device_id": "sensor-001",
      "label": "Sensor de temperatura",
      "family": "esp32",
      "capabilities": ["temperature.read", "battery.read"],
      "transport": "disabled"
    }
  ]
}
```

O manifesto permite **declarar intenção**, não relatar telemetria ou um dispositivo conectado. Nenhum arquivo é persistido; o parâmetro `--devices-preview-stdin` evita deixar conteúdos em argumentos do processo. O schema recusa endpoints, credenciais, escritas e comandos de atuadores.

## Limitações deliberadas

- Não há varredura USB, serial, BLE, MQTT, LoRa, conexão Wi-Fi, descoberta de rede, programação do Arduino/ESP32, firmware ou provisionamento.
- Nenhuma leitura de temperatura, movimento ou posição é realizada: a lista é declarativa e vazia por padrão.
- O NEXUS CORE continua um aplicativo Linux local gratuito, sem backend hospedado nem custos adicionais.
- A comunicação real, quando projetada, precisará de consentimento explícito, autenticação de nós, criptografia, isolamento e verificações físicas.

## Validação e publicação

A v0.8.0 é desenvolvida em PR **empilhado sobre a branch v0.7.3**. A v0.7.3 ainda depende de homologação física da interação X11. Sem integração ordenada, CI verde no commit final da `main` e testes físicos pertinentes, **não haverá tag nem release estável v0.8.0**.

Próximos incrementos da linha v0.8.x: transporte autenticado opt-in, telemetria limitada somente leitura, pareamento seguro e testes com Arduino/ESP32 reais. Essas capacidades **não estão implementadas na v0.8.0**.

> **Atualização de estado (10/10/2026):** o código foi integrado à `main` após v0.7.3, sem publicação de tag estável; a homologação física exigida no roadmap permanece pendente. O texto anterior descreve a dependência no momento do desenvolvimento.
