# Reloj con Listas Circulares Dobles

Taller de **Estructuras de Datos**: Universidad Cooperativa de Colombia, Campus Pasto.
Docente: Jhonatan Andrés Mideros Narváez.

Este programa es un reloj analógico con tres manecillas (hora, minuto y segundo). Está desarrollado en Python con Programación Orientada a Objetos y tiene una interfaz gráfica de escritorio. Toda su lógica se construye sobre una **lista circular doblemente enlazada** implementada desde cero.

---

## Cómo ejecutarlo

1. Tener instalado Python 3.8 o superior.
2. Abrir una terminal en esta carpeta.
3. Ejecutar:

```bash
python main.py
```

No hay que instalar nada adicional, porque `tkinter` y `time` vienen incluidos con Python.

---

## Restricciones cumplidas

| Requisito | Cómo se cumple |
|---|---|
| Solo Python | Todo el proyecto está en un único archivo `main.py` |
| Con frontend | Ventana gráfica hecha con `tkinter` |
| Sin HTML ni CSS | No se usa ninguna tecnología web |
| Sin librerías externas | Solo se usan `tkinter` (ventana) y `time` (hora del sistema), que vienen con Python. El seno y el coseno se calculan a mano con series de Taylor, sin el módulo `math` |
| Listas circulares dobles | Son la estructura principal de todo el programa |
| POO | Todo el código está organizado en clases |
| Código en inglés y reloj en español | Las clases, variables y comentarios están en inglés. La interfaz está en español |

---

## Idea principal

La **esfera del reloj es una lista circular doble** (clase `ClockRing`) con 60 eslabones (clase `ClockLink`), uno por cada marca de minuto.
Cada **manecilla es un puntero** a uno de esos eslabones:

```
        ┌──────────────────────────────────────────────┐
        ▼                                              │
     [00] ⇄ [01] ⇄ [02] ⇄ ... ⇄ [58] ⇄ [59] ───────────┘
        ▲            ▲                    ▲
     segundero     minutero             horario
```

- Para **avanzar**, la manecilla sigue `next` (sentido horario).
- Para **retroceder**, sigue `prev` (sentido antihorario).
- Como la lista es **circular**, del eslabón `59` se pasa al `00` sin ninguna condición especial.
- Como la lista es **doble**, el método `step_towards()` elige el **camino más corto**. Por ejemplo, para ir de `00` a `55` da 5 pasos con `prev` en lugar de 55 con `next`.

---

## Listas circulares dobles usadas

| Lista | Elementos | Uso |
|---|---|---|
| Esfera del reloj | 60 | Posiciones por donde se mueven las 3 manecillas |
| Manecillas | 3 | Se recorren para dibujar hora, minuto y segundo |
| Zonas horarias | 9 | Botones ◀ ▶ (`prev` / `next`). Después de la última ciudad vuelve a la primera |
| Temas de color | 5 | Medianoche, Papel, Bosque, Océano y Atardecer |
| Días de la semana | 7 | Fecha en español |
| Meses | 12 | Fecha en español |
| Alarmas | variable | Se insertan ordenadas, se buscan y se eliminan |

### Clases de la estructura

- `ClockLink`: cada eslabón de la lista. Guarda un dato y dos punteros, `prev` (anterior) y `next` (siguiente).
- `ClockRing`: la lista circular doble. Guarda la cabeza (`head`) y el tamaño (`size`).

### Operaciones de la clase `ClockRing`

| Método | Descripción |
|---|---|
| `insert_at_beginning(data)` | Inserta al inicio y el nuevo eslabón pasa a ser la cabeza |
| `insert_at_end(data)` | Inserta entre el último eslabón y la cabeza |
| `insert_sorted(data, key)` | Inserta manteniendo el orden (se usa en las alarmas) |
| `delete(data)` | Elimina un eslabón y reasigna los punteros `prev` y `next` |
| `find(condition)` | Busca el primer eslabón que cumple una condición |
| `get_link(index)` | Llega a una posición recorriendo hacia adelante o hacia atrás, según lo que sea más corto |
| `__iter__()` | Recorrido hacia adelante |
| `iter_backward()` | Recorrido hacia atrás |
| `print_list()` | Imprime la lista en consola |

---

## Funcionalidades

- **Reloj analógico** con 3 manecillas y animación al moverse.
- **Reloj digital** con la fecha completa en español, por ejemplo: *Miércoles, 21 de octubre de 2026*.
- **Zonas horarias del mundo**: Pasto, la hora del equipo, Ciudad de México, Buenos Aires, Reikiavik, Dubái, Nueva Delhi, Pekín y Tokio. Al cambiar de ciudad, las manecillas se desplazan por el camino más corto.
- **Alarmas**: se pueden agregar y eliminar. Cuando suena una, aparece un aviso que se cierra con un clic.
- **5 temas de color**.
- **Formato de 12 o 24 horas**.

### Atajos de teclado

| Tecla | Acción |
|---|---|
| ← → | Cambiar de ciudad |
| T | Cambiar el tema |
| F | Cambiar entre formato de 12 y 24 horas |

---

## Estructura del código (`main.py`)

1. **Funciones matemáticas**: `sine()` y `cosine()`, implementadas con series de Taylor.
2. **Estructura de datos**: clases `ClockLink` y `ClockRing`.
3. **Clases del dominio**:
   - `DialPosition`: una marca de la esfera.
   - `Dial`: la esfera, con sus 60 eslabones.
   - `ClockHand`: una manecilla, que es un puntero a un eslabón.
   - `TimeZone`, `Theme`, `Alarm` y `SpanishCalendar`.
4. **Interfaz**: clase `ClockApp`. Su ciclo `tick()` se ejecuta cada 30 ms. En cada ciclo lee la hora, mueve cada manecilla un eslabón hacia su objetivo, redibuja y revisa las alarmas.

> Nota: las ciudades elegidas no usan horario de verano, así que su diferencia con UTC siempre es correcta.
