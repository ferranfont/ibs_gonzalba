# Proyecto Indicador IBS (Internal Bar Strength)

Este proyecto calcula y visualiza el indicador IBS (Internal Bar Strength) para el SPY, identificando señales de compra o venta basadas en un umbral configurable.

## Descripción del Indicador IBS

El IBS mide dónde cerró el precio dentro del rango diario (High - Low).

**Fórmula:**
$$ IBS = \frac{Close - Low}{High - Low} $$

- **Valor cercano a 0:** El precio cerró cerca del mínimo del día.
- **Valor cercano a 1:** El precio cerró cerca del máximo del día.

## Componentes del Proyecto

### 1. Descarga de Datos (`impot_data.py`)
- Descarga datos históricos del SPY usando `yfinance`.
- Guarda los datos en `data/spy.csv`.

### 2. Cálculo del Indicador (`find_ibs_indicator.py`)
- Lee el archivo `data/spy.csv`.
- Calcula el valor del IBS para cada vela diaria.
- Genera un archivo con los resultados en `outputs/ibs_indicator.csv`.

### 3. Configuración (`CONFIG.PY`)
- Define los parámetros clave del proyecto.
- `THRESHOLD`: Umbral para identificar señales (por defecto 0.9). Si el IBS > THRESHOLD, se considera una señal.

### 4. Visualización y Señales (`plot_spy_data.py`)
- Lee los datos y el umbral configurado.
- Genera un gráfico interactivo (`charts/spy_chart.html`) usando `plotly`:
  - **Velas Japonesas:** Muestra la acción del precio (Velde/Rojo).
  - **Puntos Azules:** Señalan los días donde el IBS superó el umbral configurado.
- Filtra y guarda las señales detectadas en `outputs/entry_signals.csv`.
- El gráfico se abre automáticamente en el navegador.

## Estructura de Directorios

- `data/`: Contiene los datos históricos descargados (`spy.csv`).
- `outputs/`: Contiene los resultados procesados (`ibs_indicator.csv`, `entry_signals.csv`).
- `charts/`: Contiene los gráficos generados (`spy_chart.html`).
- `CONFIG.PY`: Archivo de configuración.

## Requisitos

Las dependencias necesarias se encuentran en `requirements.txt`:
- pandas
- plotly
- numpy
- yfinance
- matplotlib

## Uso

1.  **Descargar datos:**
    ```bash
    python impot_data.py
    ```
2.  **Calcular indicador (opcional, el paso 3 también lo hace):**
    ```bash
    python find_ibs_indicator.py
    ```
3.  **Generar gráfico y señales:**
    ```bash
    python plot_spy_data.py
    ```

Este comando abrirá el gráfico en tu navegador y guardará las señales encontradas en la carpeta `outputs`.
