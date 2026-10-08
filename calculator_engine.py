"""
Calculator Engine - Safe Mathematical Expression Evaluator
Dibuat dengan Python Standard Library (ast, math)
Aman dari code injection, mendukung kalkulasi saintifik, trigonometri (DEG/RAD), dan faktorial.
"""

import ast
import math
import re
from typing import Any, Tuple, Union

# Daftar fungsi yang diizinkan
ALLOWED_FUNCTIONS = {
    'sin', 'cos', 'tan',
    'asin', 'acos', 'atan',
    'sinh', 'cosh', 'tanh',
    'sqrt', 'cbrt',
    'log', 'ln', 'log2', 'log10',
    'exp', 'abs',
    'fact', 'factorial',
    'rad', 'deg'
}

# Daftar konstanta yang diizinkan
ALLOWED_CONSTANTS = {
    'pi': math.pi,
    'e': math.e,
    'tau': math.tau,
}


class SafeMathEvaluator:
    def __init__(self, angle_unit: str = 'DEG'):
        """
        :param angle_unit: 'DEG' (derajat) atau 'RAD' (radian)
        """
        self.angle_unit = angle_unit.upper()

    def _safe_sin(self, x: float) -> float:
        val = math.radians(x) if self.angle_unit == 'DEG' else x
        res = math.sin(val)
        return 0.0 if abs(res) < 1e-15 else res

    def _safe_cos(self, x: float) -> float:
        val = math.radians(x) if self.angle_unit == 'DEG' else x
        res = math.cos(val)
        return 0.0 if abs(res) < 1e-15 else res

    def _safe_tan(self, x: float) -> float:
        if self.angle_unit == 'DEG':
            # 90, 270, dsb tidak terdefinisi
            norm = abs(x) % 180
            if abs(norm - 90) < 1e-10:
                raise ValueError("Nilai tangen tidak terdefinisi pada sudut 90° + k·180°")
            val = math.radians(x)
        else:
            val = x
        res = math.tan(val)
        return 0.0 if abs(res) < 1e-15 else res

    def _safe_asin(self, x: float) -> float:
        if not (-1.0 <= x <= 1.0):
            raise ValueError("Input asin harus berada dalam rentang -1 hingga 1")
        res = math.asin(x)
        return math.degrees(res) if self.angle_unit == 'DEG' else res

    def _safe_acos(self, x: float) -> float:
        if not (-1.0 <= x <= 1.0):
            raise ValueError("Input acos harus berada dalam rentang -1 hingga 1")
        res = math.acos(x)
        return math.degrees(res) if self.angle_unit == 'DEG' else res

    def _safe_atan(self, x: float) -> float:
        res = math.atan(x)
        return math.degrees(res) if self.angle_unit == 'DEG' else res

    def _safe_sqrt(self, x: float) -> float:
        if x < 0:
            raise ValueError("Tidak dapat menghitung akar kuadrat dari bilangan negatif")
        return math.sqrt(x)

    def _safe_cbrt(self, x: float) -> float:
        return math.cbrt(x) if hasattr(math, 'cbrt') else (x ** (1.0 / 3.0) if x >= 0 else -((-x) ** (1.0 / 3.0)))

    def _safe_log10(self, x: float) -> float:
        if x <= 0:
            raise ValueError("Input logaritma harus lebih besar dari 0")
        return math.log10(x)

    def _safe_ln(self, x: float) -> float:
        if x <= 0:
            raise ValueError("Input ln harus lebih besar dari 0")
        return math.log(x)

    def _safe_log2(self, x: float) -> float:
        if x <= 0:
            raise ValueError("Input log2 harus lebih besar dari 0")
        return math.log2(x)

    def _safe_factorial(self, x: float) -> int:
        if x < 0:
            raise ValueError("Faktorial hanya terdefinisi untuk bilangan non-negatif")
        if not float(x).is_integer():
            raise ValueError("Faktorial hanya untuk bilangan bulat")
        n = int(x)
        if n > 170:
            raise OverflowError("Hasil faktorial terlalu besar (maksimal 170!)")
        return math.factorial(n)

    def get_function_map(self):
        return {
            'sin': self._safe_sin,
            'cos': self._safe_cos,
            'tan': self._safe_tan,
            'asin': self._safe_asin,
            'acos': self._safe_acos,
            'atan': self._safe_atan,
            'sinh': math.sinh,
            'cosh': math.cosh,
            'tanh': math.tanh,
            'sqrt': self._safe_sqrt,
            'cbrt': self._safe_cbrt,
            'log': self._safe_log10,
            'log10': self._safe_log10,
            'ln': self._safe_ln,
            'log2': self._safe_log2,
            'exp': math.exp,
            'abs': abs,
            'fact': self._safe_factorial,
            'factorial': self._safe_factorial,
            'rad': math.radians,
            'deg': math.degrees,
        }

    def _eval_node(self, node: ast.AST) -> Any:
        func_map = self.get_function_map()

        if isinstance(node, ast.Expression):
            return self._eval_node(node.body)

        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Tipe nilai tidak diizinkan: {type(node.value).__name__}")

        elif isinstance(node, ast.Name):
            name_lower = node.id.lower()
            if name_lower in ALLOWED_CONSTANTS:
                return ALLOWED_CONSTANTS[name_lower]
            raise ValueError(f"Variabel/simbol tidak dikenal: '{node.id}'")

        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            elif isinstance(node.op, ast.USub):
                return -operand
            raise ValueError(f"Operasi uner tidak didukung: {type(node.op).__name__}")

        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)

            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Div):
                if right == 0:
                    raise ZeroDivisionError("Tidak dapat membagi dengan nol")
                return left / right
            elif isinstance(node.op, ast.FloorDiv):
                if right == 0:
                    raise ZeroDivisionError("Tidak dapat membagi dengan nol")
                return left // right
            elif isinstance(node.op, ast.Mod):
                if right == 0:
                    raise ZeroDivisionError("Tidak dapat membagi dengan nol (modulo)")
                return left % right
            elif isinstance(node.op, ast.Pow):
                # Cegah komputasi eksponensial ekstrem yang menyebabkan DoS
                if abs(left) > 1e10 and right > 100:
                    raise OverflowError("Pangkat terlalu besar")
                if right > 1000:
                    raise OverflowError("Nilai eksponen terlalu besar")
                res = left ** right
                if isinstance(res, complex):
                    raise ValueError("Hasil menghasilkan bilangan imajiner (tidak didukung)")
                return res
            raise ValueError(f"Operator tidak didukung: {type(node.op).__name__}")

        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Panggilan fungsi bertingkat tidak diizinkan")
            func_name = node.func.id.lower()
            if func_name not in func_map:
                raise ValueError(f"Fungsi matematika tidak dikenal: '{func_name}'")

            args = [self._eval_node(arg) for arg in node.args]
            if len(args) != 1:
                raise ValueError(f"Fungsi '{func_name}' membutuhkan tepat 1 argumen")

            return func_map[func_name](args[0])

        raise ValueError(f"Struktur sintaks tidak didukung: {type(node).__name__}")

    def preprocess_expression(self, expr: str) -> str:
        """
        Membersihkan dan menstandardisasi ekspresi matematika.
        """
        expr = expr.strip()
        # Normalisasi simbol matematika umum
        expr = expr.replace('×', '*').replace('x', '*').replace('X', '*')
        expr = expr.replace('÷', '/').replace(':', '/')
        expr = expr.replace('^', '**')
        expr = expr.replace('π', 'pi')
        expr = expr.replace('√', 'sqrt')

        # Tangani persentase trailing, misal '50%' -> '(50/100)'
        expr = re.sub(r'(\d+(?:\.\d+)?)%', r'(\1/100)', expr)

        # Tangani faktorial postfix, misal '5!' -> 'fact(5)'
        # Regex berulang untuk mengantisipasi angka atau kurung yang diikuti tanda '!'
        while '!' in expr:
            # Pola untuk ekspresi dalam kurung: (...)! -> fact(...)
            new_expr = re.sub(r'\(([^()]+)\)!', r'fact(\1)', expr)
            if new_expr != expr:
                expr = new_expr
                continue
            # Pola untuk angka: 5! -> fact(5)
            new_expr = re.sub(r'(\b\d+(?:\.\d+)?|\bpi\b|\be\b)!', r'fact(\1)', expr)
            if new_expr == expr:
                # Jika tanda seru bukan operator faktorial yang valid
                expr = expr.replace('!', '')
                break
            expr = new_expr

        # Tangani perkalian implisit:
        # 1. Angka diikuti nama variabel/fungsi: 2pi -> 2*pi, 2sqrt(4) -> 2*sqrt(4), 5sin(30) -> 5*sin(30)
        expr = re.sub(r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)', r'\1*\2', expr)
        # 2. Angka diikuti kurung buka: 2(3) -> 2*(3)
        expr = re.sub(r'(\d+(?:\.\d+)?)\s*\(', r'\1*(', expr)
        # 3. Kurung tutup diikuti kurung buka: (2)(3) -> (2)*(3)
        expr = re.sub(r'\)\s*\(', r')*(', expr)
        # 4. Kurung tutup diikuti angka: (2)3 -> (2)*3
        expr = re.sub(r'\)\s*(\d+(?:\.\d+)?)', r')*\1', expr)
        # 5. Kurung tutup diikuti variabel/fungsi: (2)pi -> (2)*pi
        expr = re.sub(r'\)\s*([a-zA-Z]+)', r')*\1', expr)

        return expr

    def evaluate(self, expr: str) -> Union[int, float]:
        """
        Mengevaluasi ekspresi string dan mengembalikan hasil angka.
        """
        if not expr or expr.strip() == '':
            raise ValueError("Ekspresi tidak boleh kosong")

        processed = self.preprocess_expression(expr)
        
        try:
            tree = ast.parse(processed, mode='eval')
        except SyntaxError as e:
            raise ValueError(f"Format rumus tidak valid: {e.msg}")

        result = self._eval_node(tree)

        # Pembersihan floating point jika mendekati integer atau 0
        if isinstance(result, float):
            if math.isnan(result):
                raise ValueError("Hasil perhitungan tidak terdefinisi (NaN)")
            if math.isinf(result):
                raise OverflowError("Hasil perhitungan tak hingga (Infinity)")
            if abs(result - round(result)) < 1e-12:
                result = int(round(result))
            else:
                # Batasi desimal berulang tidak perlu
                result = round(result, 11)

        return result


def format_result(val: Union[int, float]) -> str:
    """Format angka untuk tampilan yang rapi."""
    if isinstance(val, int):
        return f"{val:,}".replace(',', '.')
    
    # Untuk float
    val_str = f"{val:.10g}"
    # Ganti titik desimal jika ingin koma atau tetap titik (standar kalkulator internasional menggunakan titik)
    return val_str


def calculate(expression: str, angle_unit: str = 'DEG') -> Tuple[bool, Any, str]:
    """
    Helper fungsi utama untuk dipanggil oleh server API.
    Returns: (success: bool, result_or_none, message: str)
    """
    evaluator = SafeMathEvaluator(angle_unit=angle_unit)
    try:
        raw_result = evaluator.evaluate(expression)
        display_str = format_result(raw_result)
        return True, raw_result, display_str
    except ZeroDivisionError as e:
        return False, None, str(e)
    except OverflowError as e:
        return False, None, str(e)
    except ValueError as e:
        return False, None, str(e)
    except Exception as e:
        return False, None, f"Kesalahan kalkulasi: {str(e)}"


if __name__ == '__main__':
    # Pengujian mandiri
    test_cases = [
        ("2 + 3 * 4", "DEG", 14),
        ("sin(30)", "DEG", 0.5),
        ("cos(60)", "DEG", 0.5),
        ("tan(45)", "DEG", 1.0),
        ("sqrt(16)", "DEG", 4),
        ("5!", "DEG", 120),
        ("2pi", "DEG", 2 * math.pi),
        ("2^3", "DEG", 8),
        ("log(100)", "DEG", 2),
        ("ln(e)", "DEG", 1),
        ("50%", "DEG", 0.5),
        ("(2+3)(4-1)", "DEG", 15),
    ]

    print("Menjalankan Unit Test Kalkulator:")
    for expr, unit, expected in test_cases:
        ok, res, msg = calculate(expr, unit)
        assert ok, f"Gagal mengevaluasi '{expr}': {msg}"
        diff = abs(res - expected)
        assert diff < 1e-9, f"Hasil '{expr}' salah: dapat {res}, harap {expected}"
        print(f"  [OK] {expr} = {msg} ({res})")
    print("Semua pengujian kalkulator berhasil!")
