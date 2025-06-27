import sqlite3
from datetime import datetime
import os
from fpdf import FPDF

#pip install fpdf /si no te funciona instala esto

# Conexión a la base de datos SQLite
conn = sqlite3.connect('panaderia.db')
cursor = conn.cursor()

# Crear tablas si no existen
def inicializar_bd():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            cantidad INTEGER NOT NULL,
            descripcion TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            direccion TEXT,
            credito_maximo REAL DEFAULT 0,
            credito_actual REAL DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            fecha TEXT NOT NULL,
            total REAL NOT NULL,
            tipo_pago TEXT NOT NULL,  -- 'contado' o 'credito'
            abonado REAL DEFAULT 0,
            saldo_pendiente REAL DEFAULT 0,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (venta_id) REFERENCES ventas(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS abonos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            cliente_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            monto REAL NOT NULL,
            FOREIGN KEY (venta_id) REFERENCES ventas(id),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario_movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,  -- 'entrada' o 'salida'
            cantidad INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            motivo TEXT,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    ''')
    
    conn.commit()

# Funciones para el menú de productos
def agregar_producto():
    print("\n--- Agregar Nuevo Producto ---")
    nombre = input("Nombre del producto: ")
    precio = float(input("Precio unitario: "))
    cantidad = int(input("Cantidad inicial en inventario: "))
    descripcion = input("Descripción (opcional): ")
    
    cursor.execute('''
        INSERT INTO productos (nombre, precio, cantidad, descripcion)
        VALUES (?, ?, ?, ?)
    ''', (nombre, precio, cantidad, descripcion))
    
    # Registrar movimiento de inventario
    cursor.execute('''
        INSERT INTO inventario_movimientos (producto_id, tipo, cantidad, fecha, motivo)
        VALUES (?, ?, ?, ?, ?)
    ''', (cursor.lastrowid, 'entrada', cantidad, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Inventario inicial'))
    
    conn.commit()
    print(f"Producto '{nombre}' agregado exitosamente!")

def modificar_producto():
    listar_productos()
    producto_id = int(input("\nID del producto a modificar: "))
    
    cursor.execute("SELECT * FROM productos WHERE id=?", (producto_id,))
    producto = cursor.fetchone()
    
    if not producto:
        print("Producto no encontrado!")
        return
    
    print(f"\nEditando producto: {producto[1]}")
    nombre = input(f"Nuevo nombre ({producto[1]}): ") or producto[1]
    precio = input(f"Nuevo precio ({producto[2]}): ") or producto[2]
    descripcion = input(f"Nueva descripción ({producto[4]}): ") or producto[4]
    
    cursor.execute('''
        UPDATE productos 
        SET nombre=?, precio=?, descripcion=?
        WHERE id=?
    ''', (nombre, float(precio), descripcion, producto_id))
    
    conn.commit()
    print("Producto actualizado exitosamente!")

def ajustar_inventario():
    listar_productos()
    producto_id = int(input("\nID del producto a ajustar: "))
    
    cursor.execute("SELECT * FROM productos WHERE id=?", (producto_id,))
    producto = cursor.fetchone()
    
    if not producto:
        print("Producto no encontrado!")
        return
    
    print(f"\nAjustando inventario de: {producto[1]}")
    print(f"Cantidad actual: {producto[3]}")
    nueva_cantidad = int(input("Nueva cantidad: "))
    motivo = input("Motivo del ajuste (entrada/salida): ")
    
    diferencia = nueva_cantidad - producto[3]
    tipo = 'entrada' if diferencia > 0 else 'salida'
    
    cursor.execute('''
        UPDATE productos 
        SET cantidad=?
        WHERE id=?
    ''', (nueva_cantidad, producto_id))
    
    # Registrar movimiento de inventario
    cursor.execute('''
        INSERT INTO inventario_movimientos (producto_id, tipo, cantidad, fecha, motivo)
        VALUES (?, ?, ?, ?, ?)
    ''', (producto_id, tipo, abs(diferencia), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), motivo))
    
    conn.commit()
    print("Inventario actualizado exitosamente!")

def listar_productos():
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    
    print("\n--- Lista de Productos ---")
    print("ID  | Nombre                | Precio  | Cantidad")
    print("-" * 50)
    for p in productos:
        print(f"{p[0]:<3} | {p[1]:<20} | ${p[2]:<6.2f} | {p[3]}")
    print("-" * 50)
    print(f"Total productos: {len(productos)}")

# Funciones para el menú de clientes
def agregar_cliente():
    print("\n--- Agregar Nuevo Cliente ---")
    nombre = input("Nombre completo: ")
    telefono = input("Teléfono: ")
    direccion = input("Dirección: ")
    credito_maximo = float(input("Límite de crédito: $") or 0)
    
    cursor.execute('''
        INSERT INTO clientes (nombre, telefono, direccion, credito_maximo)
        VALUES (?, ?, ?, ?)
    ''', (nombre, telefono, direccion, credito_maximo))
    
    conn.commit()
    print(f"Cliente '{nombre}' agregado exitosamente!")

def listar_clientes():
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()
    
    print("\n--- Lista de Clientes ---")
    print("ID  | Nombre                | Teléfono   | Crédito Máx. | Crédito Act.")
    print("-" * 80)
    for c in clientes:
        print(f"{c[0]:<3} | {c[1]:<20} | {c[2]:<10} | ${c[4]:<10.2f} | ${c[5]:<10.2f}")
    print("-" * 80)
    print(f"Total clientes: {len(clientes)}")

def buscar_cliente_por_nombre():
    nombre = input("\nNombre del cliente a buscar: ")
    cursor.execute("SELECT * FROM clientes WHERE nombre LIKE ?", (f"%{nombre}%",))
    clientes = cursor.fetchall()
    
    if not clientes:
        print("No se encontraron clientes con ese nombre.")
        return None
    
    print("\n--- Resultados de Búsqueda ---")
    print("ID  | Nombre                | Teléfono   | Crédito Máx. | Crédito Act.")
    print("-" * 80)
    for c in clientes:
        print(f"{c[0]:<3} | {c[1]:<20} | {c[2]:<10} | ${c[4]:<10.2f} | ${c[5]:<10.2f}")
    
    if len(clientes) == 1:
        return clientes[0][0]  # Retornar ID del único cliente encontrado
    
    cliente_id = int(input("\nIngrese el ID del cliente seleccionado: "))
    return cliente_id

# Funciones para ventas
def realizar_venta():
    print("\n--- Realizar Venta ---")
    
    # Preguntar si es venta al contado o crédito
    tipo_pago = input("Tipo de pago (contado/credito): ").lower()
    while tipo_pago not in ['contado', 'credito']:
        print("Opción inválida. Debe ser 'contado' o 'credito'.")
        tipo_pago = input("Tipo de pago (contado/credito): ").lower()
    
    cliente_id = None
    if tipo_pago == 'credito':
        cliente_id = buscar_cliente_por_nombre()
        if not cliente_id:
            print("Venta a crédito requiere un cliente válido.")
            return
        
        # Verificar crédito disponible
        cursor.execute("SELECT credito_maximo, credito_actual FROM clientes WHERE id=?", (cliente_id,))
        credito_max, credito_act = cursor.fetchone()
        disponible = credito_max - credito_act
        print(f"\nCrédito disponible: ${disponible:.2f}")
    
    # Mostrar productos disponibles
    cursor.execute("SELECT id, nombre, precio, cantidad FROM productos WHERE cantidad > 0 ORDER BY nombre")
    productos = cursor.fetchall()
    
    if not productos:
        print("No hay productos disponibles para vender!")
        return
    
    print("\n--- Productos Disponibles ---")
    print("ID  | Nombre                | Precio  | Cantidad")
    print("-" * 50)
    for p in productos:
        print(f"{p[0]:<3} | {p[1]:<20} | ${p[2]:<6.2f} | {p[3]}")
    
    # Proceso de selección de productos
    venta_detalle = []
    total = 0.0
    
    while True:
        producto_id = input("\nID del producto a vender (0 para terminar): ")
        if producto_id == '0':
            break
        
        try:
            producto_id = int(producto_id)
            producto = next((p for p in productos if p[0] == producto_id), None)
            
            if not producto:
                print("ID de producto inválido!")
                continue
                
            cantidad = int(input(f"Cantidad de '{producto[1]}' (max {producto[3]}): "))
            if cantidad <= 0 or cantidad > producto[3]:
                print("Cantidad inválida!")
                continue
                
            subtotal = cantidad * producto[2]
            venta_detalle.append({
                'producto_id': producto_id,
                'nombre': producto[1],
                'precio': producto[2],
                'cantidad': cantidad,
                'subtotal': subtotal
            })
            
            total += subtotal
            print(f"Agregado: {producto[1]} x {cantidad} = ${subtotal:.2f}")
            print(f"Total parcial: ${total:.2f}")
            
        except ValueError:
            print("Entrada inválida!")
    
    if not venta_detalle:
        print("No se agregaron productos. Venta cancelada.")
        return
    
    # Resumen de la venta
    print("\n--- Resumen de Venta ---")
    for item in venta_detalle:
        print(f"{item['nombre']} x {item['cantidad']} @ ${item['precio']:.2f} = ${item['subtotal']:.2f}")
    print(f"\nTOTAL: ${total:.2f}")
    
    # Procesar pago
    if tipo_pago == 'contado':
        pago = float(input("\nIngrese el monto recibido: $"))
        while pago < total:
            print("Monto insuficiente!")
            pago = float(input("Ingrese el monto recibido: $"))
        
        cambio = pago - total
        if cambio > 0:
            print(f"Cambio: ${cambio:.2f}")
        
        # Registrar venta al contado
        cursor.execute('''
            INSERT INTO ventas (cliente_id, fecha, total, tipo_pago, abonado, saldo_pendiente)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (cliente_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total, 'contado', total, 0))
        
    else:  # Crédito
        print("\nVenta a crédito registrada.")
        abono_inicial = float(input("Abono inicial (opcional, enter para $0): $") or 0)
        
        # Registrar venta a crédito
        cursor.execute('''
            INSERT INTO ventas (cliente_id, fecha, total, tipo_pago, abonado, saldo_pendiente)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (cliente_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total, 'credito', abono_inicial, total - abono_inicial))
        
        # Actualizar crédito del cliente
        cursor.execute('''
            UPDATE clientes 
            SET credito_actual = credito_actual + ?
            WHERE id = ?
        ''', (total - abono_inicial, cliente_id))
        
        if abono_inicial > 0:
            # Registrar abono
            venta_id = cursor.lastrowid
            cursor.execute('''
                INSERT INTO abonos (venta_id, cliente_id, fecha, monto)
                VALUES (?, ?, ?, ?)
            ''', (venta_id, cliente_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), abono_inicial))
    
    # Registrar detalle de venta
    venta_id = cursor.lastrowid
    for item in venta_detalle:
        cursor.execute('''
            INSERT INTO ventas_detalle (venta_id, producto_id, cantidad, precio_unitario, subtotal)
            VALUES (?, ?, ?, ?, ?)
        ''', (venta_id, item['producto_id'], item['cantidad'], item['precio'], item['subtotal']))
        
        # Actualizar inventario
        cursor.execute('''
            UPDATE productos 
            SET cantidad = cantidad - ?
            WHERE id = ?
        ''', (item['cantidad'], item['producto_id']))
        
        # Registrar movimiento de inventario
        cursor.execute('''
            INSERT INTO inventario_movimientos (producto_id, tipo, cantidad, fecha, motivo)
            VALUES (?, ?, ?, ?, ?)
        ''', (item['producto_id'], 'salida', item['cantidad'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Venta'))
    
    conn.commit()
    print("\nVenta registrada exitosamente!")

def registrar_abono():
    print("\n--- Registrar Abono a Crédito ---")
    cliente_id = buscar_cliente_por_nombre()
    if not cliente_id:
        return
    
    # Mostrar deudas del cliente
    cursor.execute('''
        SELECT v.id, v.fecha, v.total, v.abonado, v.saldo_pendiente
        FROM ventas v
        WHERE v.cliente_id = ? AND v.saldo_pendiente > 0
        ORDER BY v.fecha
    ''', (cliente_id,))
    deudas = cursor.fetchall()
    
    if not deudas:
        print("El cliente no tiene deudas pendientes.")
        return
    
    print("\n--- Deudas Pendientes ---")
    print("ID Venta | Fecha            | Total   | Abonado | Saldo Pend.")
    print("-" * 60)
    for d in deudas:
        print(f"{d[0]:<8} | {d[1]:<16} | ${d[2]:<6.2f} | ${d[3]:<6.2f} | ${d[4]:<6.2f}")
    
    venta_id = int(input("\nID de la venta a abonar: "))
    venta_seleccionada = next((d for d in deudas if d[0] == venta_id), None)
    
    if not venta_seleccionada:
        print("ID de venta inválido!")
        return
    
    monto_max = venta_seleccionada[4]
    monto = float(input(f"Monto a abonar (max ${monto_max:.2f}): $"))
    
    while monto <= 0 or monto > monto_max:
        print("Monto inválido!")
        monto = float(input(f"Monto a abonar (max ${monto_max:.2f}): $"))
    
    # Registrar abono
    cursor.execute('''
        INSERT INTO abonos (venta_id, cliente_id, fecha, monto)
        VALUES (?, ?, ?, ?)
    ''', (venta_id, cliente_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), monto))
    
    # Actualizar venta
    nuevo_abonado = venta_seleccionada[3] + monto
    nuevo_saldo = venta_seleccionada[4] - monto
    
    cursor.execute('''
        UPDATE ventas 
        SET abonado = ?, saldo_pendiente = ?
        WHERE id = ?
    ''', (nuevo_abonado, nuevo_saldo, venta_id))
    
    # Actualizar crédito del cliente
    cursor.execute('''
        UPDATE clientes 
        SET credito_actual = credito_actual - ?
        WHERE id = ?
    ''', (monto, cliente_id))
    
    conn.commit()
    print(f"\nAbono de ${monto:.2f} registrado exitosamente!")
    print(f"Nuevo saldo pendiente: ${nuevo_saldo:.2f}")

# Funciones para reportes
def generar_reporte_ventas_diarias():
    fecha = input("\nFecha para el reporte (YYYY-MM-DD, enter para hoy): ") or datetime.now().strftime("%Y-%m-%d")
    
    # Obtener ventas del día
    cursor.execute('''
        SELECT v.id, v.fecha, c.nombre, v.total, v.tipo_pago, v.abonado, v.saldo_pendiente
        FROM ventas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        WHERE DATE(v.fecha) = ?
        ORDER BY v.fecha
    ''', (fecha,))
    ventas = cursor.fetchall()
    
    # Calcular totales
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN tipo_pago = 'contado' THEN total ELSE 0 END) as total_contado,
            SUM(CASE WHEN tipo_pago = 'credito' THEN total ELSE 0 END) as total_credito,
            SUM(total) as total_general,
            SUM(abonado) as total_abonado
        FROM ventas
        WHERE DATE(fecha) = ?
    ''', (fecha,))
    totales = cursor.fetchone()
    
    # Crear PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Reporte de Ventas - {fecha}", 0, 1, 'C')
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 10, "="*80, 0, 1)
    
    # Detalle de ventas
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Detalle de Ventas:", 0, 1)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(15, 6, "ID", 1)
    pdf.cell(30, 6, "Fecha", 1)
    pdf.cell(40, 6, "Cliente", 1)
    pdf.cell(20, 6, "Total", 1)
    pdf.cell(20, 6, "Tipo Pago", 1)
    pdf.cell(20, 6, "Abonado", 1)
    pdf.cell(25, 6, "Saldo Pend.", 1)
    pdf.ln()
    
    pdf.set_font("Arial", '', 8)
    for v in ventas:
        pdf.cell(15, 6, str(v[0]), 1)
        pdf.cell(30, 6, v[1][11:19], 1)  # Solo hora
        pdf.cell(40, 6, v[2] if v[2] else "Contado", 1)
        pdf.cell(20, 6, f"${v[3]:.2f}", 1)
        pdf.cell(20, 6, v[4].capitalize(), 1)
        pdf.cell(20, 6, f"${v[5]:.2f}", 1)
        pdf.cell(25, 6, f"${v[6]:.2f}", 1)
        pdf.ln()
    
    # Totales
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, "="*80, 0, 1)
    pdf.cell(0, 6, f"Total Ventas al Contado: ${totales[0] or 0:.2f}", 0, 1)
    pdf.cell(0, 6, f"Total Ventas a Crédito: ${totales[1] or 0:.2f}", 0, 1)
    pdf.cell(0, 6, f"Total General: ${totales[2] or 0:.2f}", 0, 1)
    pdf.cell(0, 6, f"Total Abonado: ${totales[3] or 0:.2f}", 0, 1)
    
    # Guardar PDF
    nombre_archivo = f"Reporte_Ventas_{fecha.replace('-', '')}.pdf"
    pdf.output(nombre_archivo)
    print(f"\nReporte generado exitosamente: {nombre_archivo}")
    os.startfile(nombre_archivo)

def generar_reporte_inventario():
    # Obtener productos
    cursor.execute("SELECT id, nombre, precio, cantidad FROM productos ORDER BY nombre")
    productos = cursor.fetchall()
    
    # Obtener movimientos recientes
    cursor.execute('''
        SELECT p.nombre, im.tipo, im.cantidad, im.fecha, im.motivo
        FROM inventario_movimientos im
        JOIN productos p ON im.producto_id = p.id
        ORDER BY im.fecha DESC
        LIMIT 20
    ''')
    movimientos = cursor.fetchall()
    
    # Crear PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Reporte de Inventario", 0, 1, 'C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
    
    # Lista de productos
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Inventario Actual:", 0, 1)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(15, 6, "ID", 1)
    pdf.cell(60, 6, "Producto", 1)
    pdf.cell(30, 6, "Precio", 1)
    pdf.cell(20, 6, "Cantidad", 1)
    pdf.cell(30, 6, "Valor Total", 1)
    pdf.ln()
    
    pdf.set_font("Arial", '', 8)
    valor_total = 0
    for p in productos:
        valor = p[2] * p[3]
        valor_total += valor
        pdf.cell(15, 6, str(p[0]), 1)
        pdf.cell(60, 6, p[1], 1)
        pdf.cell(30, 6, f"${p[2]:.2f}", 1)
        pdf.cell(20, 6, str(p[3]), 1)
        pdf.cell(30, 6, f"${valor:.2f}", 1)
        pdf.ln()
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(105, 6, "Total Valor Inventario:", 1)
    pdf.cell(30, 6, f"${valor_total:.2f}", 1, 0, 'R')
    pdf.ln(10)
    
    # Movimientos recientes
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Últimos Movimientos:", 0, 1)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(60, 6, "Producto", 1)
    pdf.cell(20, 6, "Tipo", 1)
    pdf.cell(20, 6, "Cantidad", 1)
    pdf.cell(40, 6, "Fecha", 1)
    pdf.cell(40, 6, "Motivo", 1)
    pdf.ln()
    
    pdf.set_font("Arial", '', 8)
    for m in movimientos:
        pdf.cell(60, 6, m[0], 1)
        pdf.cell(20, 6, m[1].capitalize(), 1)
        pdf.cell(20, 6, str(m[2]), 1)
        pdf.cell(40, 6, m[3], 1)
        pdf.cell(40, 6, m[4], 1)
        pdf.ln()
    
    # Guardar PDF
    nombre_archivo = f"Reporte_Inventario_{datetime.now().strftime('%Y%m%d')}.pdf"
    pdf.output(nombre_archivo)
    print(f"\nReporte generado exitosamente: {nombre_archivo}")
    os.startfile(nombre_archivo)

# Menú principal
def menu_principal():
    while True:
        print("\n--- SISTEMA DE PANADERÍA ---")
        print("1. Gestión de Productos")
        print("2. Gestión de Clientes")
        print("3. Punto de Venta")
        print("4. Reportes")
        print("5. Salir")
        
        opcion = input("\nSeleccione una opción: ")
        
        if opcion == '1':
            menu_productos()
        elif opcion == '2':
            menu_clientes()
        elif opcion == '3':
            menu_ventas()
        elif opcion == '4':
            menu_reportes()
        elif opcion == '5':
            print("\nSaliendo del sistema...")
            conn.close()
            break
        else:
            print("Opción inválida. Intente nuevamente.")

def menu_productos():
    while True:
        print("\n--- GESTIÓN DE PRODUCTOS ---")
        print("1. Agregar Producto")
        print("2. Modificar Producto")
        print("3. Ajustar Inventario")
        print("4. Listar Productos")
        print("5. Volver al menú principal")
        
        opcion = input("\nSeleccione una opción: ")
        
        if opcion == '1':
            agregar_producto()
        elif opcion == '2':
            modificar_producto()
        elif opcion == '3':
            ajustar_inventario()
        elif opcion == '4':
            listar_productos()
        elif opcion == '5':
            break
        else:
            print("Opción inválida. Intente nuevamente.")

def menu_clientes():
    while True:
        print("\n--- GESTIÓN DE CLIENTES ---")
        print("1. Agregar Cliente")
        print("2. Listar Clientes")
        print("3. Buscar Cliente")
        print("4. Volver al menú principal")
        
        opcion = input("\nSeleccione una opción: ")
        
        if opcion == '1':
            agregar_cliente()
        elif opcion == '2':
            listar_clientes()
        elif opcion == '3':
            buscar_cliente_por_nombre()
        elif opcion == '4':
            break
        else:
            print("Opción inválida. Intente nuevamente.")

def menu_ventas():
    while True:
        print("\n--- PUNTO DE VENTA ---")
        print("1. Realizar Venta")
        print("2. Registrar Abono")
        print("3. Volver al menú principal")
        
        opcion = input("\nSeleccione una opción: ")
        
        if opcion == '1':
            realizar_venta()
        elif opcion == '2':
            registrar_abono()
        elif opcion == '3':
            break
        else:
            print("Opción inválida. Intente nuevamente.")

def menu_reportes():
    while True:
        print("\n--- REPORTES ---")
        print("1. Reporte de Ventas Diarias")
        print("2. Reporte de Inventario")
        print("3. Volver al menú principal")
        
        opcion = input("\nSeleccione una opción: ")
        
        if opcion == '1':
            generar_reporte_ventas_diarias()
        elif opcion == '2':
            generar_reporte_inventario()
        elif opcion == '3':
            break
        else:
            print("Opción inválida. Intente nuevamente.")

# Iniciar sistema
if __name__ == "__main__":
    inicializar_bd()
    menu_principal()