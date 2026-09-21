# 🏢 Busca Inmuebles - Agregador y Comparador Multicanal

Aplicación web local para buscar, centralizar, deduplicar y comparar inmuebles en venta en **CABA (todos los 48 barrios)** y **Gran Buenos Aires (Norte, Sur, Oeste)** desde los principales portales:
- 🟡 **Mercado Libre Inmuebles**
- 🟣 **Zonaprop**
- 🔵 **Argenprop**
- 🟢 **Properati**

---

## ✨ Características Principales

1. **Filtros Avanzados (Estilo Mercado Libre)**:
   - **Tipo de Inmueble**: Departamentos, Casas, PH.
   - **Rango de Precio en USD**: Sliders, inputs de mínimo y máximo, y accesos directos.
   - **Rango de Superficie ($m^2$)**: Superficie total y cálculo automático de precio por $m^2$.
   - **Multi-selección de Barrios**: Catálogo completo de CABA y GBA con búsqueda instantánea y selección múltiple.
   - **Dormitorios y Baños**: Filtros por cantidad de dormitorios (1, 2, 3, 4+) y baños (1, 2, 3+).
   - **Fecha de Publicación**: Filtro por novedades (Hoy, últimos 7 días, 15 días, 30 días).
   - **Portales**: Filtrar por uno o varios portales a la vez.

2. **Detección Inteligente de Duplicados**:
   - Motor de agrupamiento algorítmico que identifica la misma propiedad publicada en varios portales o por distintas inmobiliarias.
   - Botón para comparar precios entre las publicaciones y acceder directamente a cada enlace.

3. **Favoritos y Notas Personales**:
   - Guardar inmuebles favoritos con ⭐.
   - Agregar notas personalizadas (ej. *'Contactar a inmobiliaria los martes'*).
   - Descartar inmuebles no deseados con 🗑️.

4. **Exportación a Excel (.xlsx)**:
   - Exporta con un solo clic todos los inmuebles filtrados con columnas detalladas, precio por $m^2$, barrio, fecha y **enlaces web clickeables**.

5. **Panel de Escaneo y Actualización**:
   - Disparador de escaneos a demanda por portal, tipo de propiedad y zona.
   - Historial de ejecuciones y estado en tiempo real.

---

## 🚀 Cómo Iniciar la Aplicación

Simplemente hacé **doble clic en `start_app.bat`** (o `iniciar_buscador.bat`) en la carpeta principal.

Esto levantará automáticamente:
- **Backend FastAPI**: `http://127.0.0.1:8000` (con documentación Swagger en `/docs`)
- **Frontend Web**: `http://localhost:5173`
- Abrirá tu navegador automáticamente.
