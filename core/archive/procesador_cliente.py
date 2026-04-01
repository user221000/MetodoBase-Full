"""Validación, normalización y captura de datos del cliente."""
import os
from datetime import datetime

from config.constantes import (
    FACTORES_ACTIVIDAD, NIVELES_ACTIVIDAD, OBJETIVOS_VALIDOS, CARPETA_SALIDA,
    CARPETA_PLANES,
)
from core.modelos import ClienteEvaluacion
from core.motor_nutricional import MotorNutricional


# ============================================================================
# VALIDADOR
# ============================================================================

class ValidadorCliente:
    """Valida datos según reglas de negocio del gym."""
    
    @staticmethod
    def validar_cliente(cliente: ClienteEvaluacion) -> tuple[bool, list[str]]:
        errores = []
        
        if not cliente.nombre or not isinstance(cliente.nombre, str) or len(cliente.nombre.strip()) == 0:
            errores.append("ERROR: Nombre: Requerido y debe ser texto válido")
        
        if not isinstance(cliente.edad, (int, float)) or cliente.edad < 14 or cliente.edad > 80:
            errores.append(f"ERROR: Edad: Debe estar entre 14 y 80 años (actual: {cliente.edad})")
        
        if not isinstance(cliente.peso_kg, (int, float)) or cliente.peso_kg <= 30:
            errores.append(f"ERROR: Peso: Debe ser mayor a 30 kg (actual: {cliente.peso_kg})")
        
        if not isinstance(cliente.estatura_cm, (int, float)) or cliente.estatura_cm < 100 or cliente.estatura_cm > 230:
            errores.append(f"ERROR: Estatura: Debe estar entre 100 y 230 cm (actual: {cliente.estatura_cm})")
        
        if not isinstance(cliente.grasa_corporal_pct, (int, float)) or cliente.grasa_corporal_pct < 3 or cliente.grasa_corporal_pct > 60:
            errores.append(f"ERROR: Grasa Corporal: Debe estar entre 3% y 60% (actual: {cliente.grasa_corporal_pct}%)")
        
        if cliente.nivel_actividad.lower() not in NIVELES_ACTIVIDAD:
            errores.append(f"ERROR: Nivel Actividad: Debe ser uno de {NIVELES_ACTIVIDAD} (actual: {cliente.nivel_actividad})")
        
        if cliente.objetivo.lower() not in OBJETIVOS_VALIDOS:
            errores.append(f"ERROR: Objetivo: Debe ser uno de {OBJETIVOS_VALIDOS} (actual: {cliente.objetivo})")
        
        es_valido = len(errores) == 0
        return es_valido, errores


# ============================================================================
# NORMALIZADOR
# ============================================================================

class NormalizadorCliente:
    """Normaliza datos del cliente."""
    
    @staticmethod
    def normalizar(cliente: ClienteEvaluacion) -> ClienteEvaluacion:
        try:
            cliente.peso_kg = float(cliente.peso_kg)
            cliente.estatura_cm = float(cliente.estatura_cm)
            cliente.grasa_corporal_pct = float(cliente.grasa_corporal_pct)
            cliente.edad = int(cliente.edad)
        except (ValueError, TypeError) as e:
            cliente.errores.append(f"ERROR: Conversión: Error al convertir a números: {str(e)}")
            return cliente
        
        cliente.nombre = cliente.nombre.strip() if isinstance(cliente.nombre, str) else ""
        cliente.nivel_actividad = cliente.nivel_actividad.lower().strip()
        cliente.objetivo = cliente.objetivo.lower().strip()
        cliente.factor_actividad = FACTORES_ACTIVIDAD.get(cliente.nivel_actividad, 1.2)
        
        return cliente


# ============================================================================
# CAPTURADOR DE DATOS (CLI interactivo)
# ============================================================================

class CapturadorDatos:
    """Captura datos del usuario de forma interactiva."""
    
    @staticmethod
    def solicitar_nombre() -> str:
        while True:
            nombre = input("Ingresa nombre del cliente: ").strip()
            if nombre and len(nombre) > 0:
                return nombre
            print("  WARN:  El nombre no puede estar vacío. Intenta de nuevo.")
    
    @staticmethod
    def solicitar_edad() -> int:
        while True:
            try:
                edad = int(input("Ingresa edad (14-80): "))
                if 14 <= edad <= 80:
                    return edad
                print(f"  WARN:  La edad debe estar entre 14 y 80. Intenta de nuevo.")
            except ValueError:
                print("  WARN:  Ingresa un número válido para la edad.")
    
    @staticmethod
    def solicitar_peso() -> float:
        while True:
            try:
                peso = float(input("Ingresa peso (kg) [>30]: "))
                if peso > 30:
                    return peso
                print(f"  WARN:  El peso debe ser mayor a 30 kg. Intenta de nuevo.")
            except ValueError:
                print("  WARN:  Ingresa un número válido para el peso.")
    
    @staticmethod
    def solicitar_estatura() -> float:
        while True:
            try:
                estatura = float(input("Ingresa estatura (cm) [100-230]: "))
                if 100 <= estatura <= 230:
                    return estatura
                print(f"  WARN:  La estatura debe estar entre 100 y 230 cm. Intenta de nuevo.")
            except ValueError:
                print("  WARN:  Ingresa un número válido para la estatura.")
    
    @staticmethod
    def solicitar_grasa_corporal() -> float:
        while True:
            try:
                grasa = float(input("Ingresa % de grasa corporal [3-60]: "))
                if 3 <= grasa <= 60:
                    return grasa
                print(f"  WARN:  El % de grasa debe estar entre 3% y 60%. Intenta de nuevo.")
            except ValueError:
                print("  WARN:  Ingresa un número válido para % grasa corporal.")
    
    @staticmethod
    def solicitar_nivel_actividad() -> str:
        opciones = list(NIVELES_ACTIVIDAD)
        print(f"  Opciones de actividad: {', '.join(opciones)}")
        while True:
            actividad = input(f"Ingresa nivel de actividad ({'/'.join(opciones)}): ").lower().strip()
            if actividad in opciones:
                return actividad
            print(f"  WARN:  Selecciona una opción válida.")
    
    @staticmethod
    def solicitar_objetivo() -> str:
        opciones = list(OBJETIVOS_VALIDOS)
        print(f"  Opciones de objetivo: {', '.join(opciones)}")
        while True:
            objetivo = input(f"Ingresa objetivo ({'/'.join(opciones)}): ").lower().strip()
            if objetivo in opciones:
                return objetivo
            print(f"  WARN:  Selecciona una opción válida.")


# ============================================================================
# PROCESADOR DE EVALUACIÓN (Orquestador CLI completo)
# ============================================================================

class ProcesadorEvaluacion:
    """Orquesta todo el flujo de evaluación del cliente."""
    
    def __init__(self):
        self.validador = ValidadorCliente()
        self.normalizador = NormalizadorCliente()
        self.capturador = CapturadorDatos()
        from src.gestor_bd import GestorBDClientes
        self.bd = GestorBDClientes()
    
    def crear_cliente_interactivo(self) -> ClienteEvaluacion:
        """Ejecuta el flujo completo: captura → valida → motor → plan → PDF → BD."""
        from core.generador_planes import ConstructorPlanNuevo
        from core.exportador_salida import GeneradorPDFProfesional, GeneradorSalida
        
        print("\n" + "=" * 70)
        print("[GYMS] MVP GYMS - EVALUACIÓN DE NUEVO CLIENTE")
        print("=" * 70)
        
        print("\n[BÚSQUEDA] Verificando cliente en BD...")
        nombre = self.capturador.solicitar_nombre()
        
        cliente_existe = self.bd.buscar_por_nombre(nombre)
        
        if cliente_existe:
            print(f"      ℹ️ Cliente encontrado en BD!")
            cliente = ClienteEvaluacion()
            cliente.id_cliente = cliente_existe['id_cliente']
            cliente.nombre = nombre
            cliente.edad = cliente_existe['edad']
            cliente.peso_kg = cliente_existe['peso_kg']
            cliente.estatura_cm = cliente_existe['estatura_cm']
            cliente.grasa_corporal_pct = cliente_existe['grasa_corporal_pct']
            cliente.nivel_actividad = cliente_existe['nivel_actividad']
            cliente.objetivo = cliente_existe['objetivo']
            
            print(f"      ✅ ID: {cliente.id_cliente}")
            print(f"      📊 Planes anteriores: {self.bd.obtener_estadisticas(cliente.id_cliente)['total_planes']}")
        else:
            print(f"      ✨ Nuevo cliente")
            cliente = ClienteEvaluacion()
            cliente.nombre = nombre
            print(f"      ✅ ID asignado: {cliente.id_cliente}")
        
        print("\n[2/5] INPUT: Capturando datos básicos...")
        
        if not cliente_existe:
            cliente.edad = self.capturador.solicitar_edad()
            cliente.peso_kg = self.capturador.solicitar_peso()
            cliente.estatura_cm = self.capturador.solicitar_estatura()
            cliente.grasa_corporal_pct = self.capturador.solicitar_grasa_corporal()
            cliente.nivel_actividad = self.capturador.solicitar_nivel_actividad()
            cliente.objetivo = self.capturador.solicitar_objetivo()
            print("      OK Datos capturados correctamente")
        else:
            print(f"      ℹ️ Datos anteriores:")
            print(f"         Edad: {cliente.edad} | Peso: {cliente.peso_kg}kg | Objetivo: {cliente.objetivo}")
            cambiar = input("\n      ¿Deseas cambiar algún dato? (s/n): ").lower().strip()
            
            if cambiar == 's':
                print("\n      Ingresa los nuevos datos (deja en blanco para mantener anterior):")
                edad_input = input("      Edad (14-80): ").strip()
                if edad_input:
                    cliente.edad = int(edad_input)
                peso_input = input("      Peso (kg) [>30]: ").strip()
                if peso_input:
                    cliente.peso_kg = float(peso_input)
                estatura_input = input("      Estatura (cm) [100-230]: ").strip()
                if estatura_input:
                    cliente.estatura_cm = float(estatura_input)
                grasa_input = input("      Grasa corporal % [3-60]: ").strip()
                if grasa_input:
                    cliente.grasa_corporal_pct = float(grasa_input)
                actividad_input = input("      Nivel de actividad (nula/leve/moderada/intensa): ").strip()
                if actividad_input:
                    cliente.nivel_actividad = actividad_input
                objetivo_input = input("      Objetivo (deficit/mantenimiento/superavit): ").strip()
                if objetivo_input:
                    cliente.objetivo = objetivo_input
                print("      ✅ Datos actualizados")
            else:
                print("      ✅ Manteniendo datos anteriores")
        
        print("\n[3/5] VALIDAR: Verificando datos...")
        es_valido, errores = self.validador.validar_cliente(cliente)
        if not es_valido:
            print("      ERROR: Errores encontrados:")
            for error in errores:
                print(f"         {error}")
            return cliente
        
        print("      OK Todos los datos son válidos")
        cliente.validado = True
        cliente = self.normalizador.normalizar(cliente)
        
        print("\n[4/5] MOTOR: Calculando (Katch-McArdle)...")
        cliente = MotorNutricional.calcular_motor(cliente)
        print("      OK Motor ejecutado")
        
        print("\n[5/5] PLAN: Generando (modo determinista con rotación)...")
        stats = self.bd.obtener_estadisticas(cliente.id_cliente)
        plan_numero = stats['total_planes'] + 1
        print(f"      Plan #{plan_numero} para este cliente")
        
        plan = ConstructorPlanNuevo.construir(cliente, plan_numero=plan_numero)
        
        print("\n📄 PDF: Generando...")
        if not os.path.exists(CARPETA_SALIDA):
            os.makedirs(CARPETA_SALIDA)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_pdf = f"plan_{cliente.id_cliente}_{timestamp}.pdf"
        ruta_pdf_completa = os.path.join(CARPETA_SALIDA, nombre_pdf)
        
        generador_pdf = GeneradorPDFProfesional(ruta_pdf_completa)
        ruta_pdf = generador_pdf.generar(cliente, plan)
        print(f"      OK {ruta_pdf}")
        
        if ruta_pdf:
            try:
                os.startfile(ruta_pdf)
                print("      PDF abierto automaticamente")
            except Exception as e:
                print(f"      No se pudo abrir el PDF: {e}")
        
        print("\n📊 JSON: Generando...")
        nombre_json = f"plan_{cliente.id_cliente}_{timestamp}.json"
        
        generador = GeneradorSalida()
        resultado_dict = generador.a_dict(cliente, plan)
        os.makedirs(CARPETA_PLANES, exist_ok=True)
        ruta_json = generador.guardar_json(
            resultado_dict, os.path.join(CARPETA_PLANES, nombre_json)
        )
        print(f"      OK {ruta_json}")
        
        print("\n💾 BD: Registrando...")
        if not cliente_existe:
            self.bd.crear_cliente({
                'id_cliente': cliente.id_cliente,
                'nombre': cliente.nombre,
                'fecha_creacion': cliente.fecha_creacion,
                'edad': cliente.edad,
                'peso_kg': cliente.peso_kg,
                'estatura_cm': cliente.estatura_cm,
                'grasa_corporal_pct': cliente.grasa_corporal_pct,
                'nivel_actividad': cliente.nivel_actividad,
                'objetivo': cliente.objetivo,
                'kcal_objetivo': cliente.kcal_objetivo
            })
            print("      OK Cliente creado en BD")
        
        comidas_validas = ['desayuno', 'almuerzo', 'comida', 'cena']
        kcal_real = sum(plan[c].get('kcal_real', 0) for c in comidas_validas if c in plan)
        desv = abs(kcal_real - cliente.kcal_objetivo) / cliente.kcal_objetivo * 100
        self.bd.registrar_plan(cliente.id_cliente, ruta_pdf, ruta_json, kcal_real, desv)
        print("      OK Plan registrado en BD")
        
        print("\n" + "=" * 70)
        print("✅ FLUJO COMPLETADO")
        print("=" * 70)
        print(f"Cliente: {cliente.nombre} (ID: {cliente.id_cliente})")
        print(f"Plan: #{plan_numero} | Kcal: {kcal_real:.0f} | Desv: {desv:.1f}%")
        print(f"PDF: {ruta_pdf}")
        print(f"JSON: {ruta_json}")
        print("=" * 70 + "\n")
        
        return cliente
