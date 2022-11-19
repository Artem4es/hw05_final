from datetime import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    return {
        'year': int(datetime.now().strftime("%Y")),
    }
