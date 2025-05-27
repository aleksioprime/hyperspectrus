# desk/tests/ui/session/test_process_worker.py
import pytest
import numpy as np
from unittest.mock import patch, MagicMock, PropertyMock, call
import os

# Импортируем класс для тестирования
from desk.src.ui.session.process_worker import ProcessWorker
# Импортируем модели, которые могут понадобиться для моков
from desk.src.db.models import Chromophore, RawImage, Spectrum, OverlapCoefficient, Result, ReconstructedImage

# Путь к тестовым данным (если понадобятся файлы)
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

# --- Фикстуры ---

@pytest.fixture
def mock_pyqt_signals(mocker):
    """Мокирует сигналы PyQt для ProcessWorker."""
    mocker.patch.object(ProcessWorker, 'progress', new_callable=PropertyMock)
    mocker.patch.object(ProcessWorker, 'finished', new_callable=PropertyMock)
    mocker.patch.object(ProcessWorker, 'error', new_callable=PropertyMock)

@pytest.fixture
def base_mocks(mocker, mock_pyqt_signals):
    """
    Базовый набор моков для ProcessWorker, покрывающий основные внешние зависимости.
    Возвращает словарь с моками.
    """
    mocks = {
        'SessionLocal': mocker.patch('desk.src.ui.session.process_worker.SessionLocal'),
        'Image_open': mocker.patch('desk.src.ui.session.process_worker.Image.open'),
        'Image_fromarray': mocker.patch('desk.src.ui.session.process_worker.Image.fromarray'),
        'os_path_join': mocker.patch('os.path.join'), # Мокируем os.path.join напрямую
        'os_makedirs': mocker.patch('os.makedirs'),
        'os_path_dirname': mocker.patch('os.path.dirname', return_value='/fake/dir'), # Для base_photo_dir
        'os_path_isfile': mocker.patch('os.path.isfile', return_value=True), # По умолчанию файлы существуют
        'os_remove': mocker.patch('os.remove'),
        'uuid_uuid4': mocker.patch('uuid.uuid4', return_value=MagicMock(hex='testuuid')), # Мок для uuid
        'np_linalg_lstsq': mocker.patch('numpy.linalg.lstsq'), # Мокируем np.linalg.lstsq
        'cv2_threshold': mocker.patch('cv2.threshold'), # Мокируем cv2.threshold
        'skimage_gaussian': mocker.patch('skimage.filters.gaussian'), # Мокируем skimage.filters.gaussian
        'skimage_threshold_otsu': mocker.patch('skimage.filters.threshold_otsu') # Мокируем skimage.filters.threshold_otsu
    }

    # Настройка базового поведения для моков
    mock_db_session = MagicMock()
    mocks['SessionLocal'].return_value = mock_db_session
    mocks['db_session'] = mock_db_session # Для удобного доступа в тестах

    # np.linalg.lstsq должен возвращать кортеж (x_vec, residuals, rank, s)
    # x_vec должен иметь размерность (n_chroms,)
    # Пусть по умолчанию у нас 2 хромофора для простоты в некоторых тестах
    mocks['np_linalg_lstsq'].return_value = (np.array([0.1, 0.2]), [], 2, [])


    # Мок для Image.open().convert().size и np.array(Image.open().convert())
    mock_image_instance = MagicMock()
    mock_image_instance.size = (10, 10) # W, H
    mock_image_instance.convert.return_value = mock_image_instance # .convert() возвращает тот же мок
    mocks['Image_open'].return_value = mock_image_instance
    
    # Мок для Image.fromarray().save()
    mock_image_fromarray_instance = MagicMock()
    mocks['Image_fromarray'].return_value = mock_image_fromarray_instance
    
    # Мок для skimage.filters.gaussian
    # Он должен возвращать ndarray того же типа и формы, что и входной
    mocks['skimage_gaussian'].side_effect = lambda x, sigma, preserve_range: x.astype(np.float32)

    # Мок для cv2.threshold
    # Возвращает (пороговое_значение, бинарное_изображение)
    # Пусть по умолчанию порог будет 128, а изображение - массив нулей
    mocks['cv2_threshold'].return_value = (128, np.zeros((10,10), dtype=np.uint8))

    return mocks

@pytest.fixture
def worker(base_mocks):
    """Фикстура для создания экземпляра ProcessWorker с базовыми моками."""
    # session_id может быть любым для теста
    _worker = ProcessWorker(session_id="test_session_id")
    
    # Прикрепляем моки к экземпляру worker для удобства доступа в тестах, если нужно
    _worker.mocks = base_mocks
    return _worker

# --- Вспомогательные функции для создания мок-данных ---

def create_mock_raw_image(file_path="fake_path.png", wavelength=500, spectrum_id=1):
    """Создает мок объекта RawImage."""
    mock = MagicMock(spec=RawImage)
    mock.file_path = file_path
    mock.spectrum = MagicMock(spec=Spectrum)
    mock.spectrum.wavelength = wavelength
    mock.spectrum_id = spectrum_id
    return mock

def create_mock_chromophore(id_val, symbol_val):
    """Создает мок объекта Chromophore."""
    mock = MagicMock(spec=Chromophore)
    mock.id = id_val
    mock.symbol = symbol_val
    return mock

def create_mock_overlap_coefficient(spectrum_id_val, chromophore_id_val, coefficient_val):
    """Создает мок объекта OverlapCoefficient."""
    mock = MagicMock(spec=OverlapCoefficient)
    mock.spectrum_id = spectrum_id_val
    mock.chromophore_id = chromophore_id_val
    mock.coefficient = coefficient_val
    return mock

# --- Тесты ---

def test_process_worker_initialization(worker):
    """Проверяет, что ProcessWorker инициализируется без ошибок."""
    assert worker is not None
    assert worker.session_id == "test_session_id"
    # Проверка мокированных сигналов (что они были установлены)
    assert isinstance(worker.progress, PropertyMock)
    assert isinstance(worker.finished, PropertyMock)
    assert isinstance(worker.error, PropertyMock)

def test_run_no_raw_images(worker):
    """Тестирует случай, когда нет сырых снимков для обработки."""
    worker.mocks['db_session'].query(RawImage).filter_by.return_value.options.return_value.all.return_value = []
    
    worker.run()
    
    worker.finished.emit.assert_called_once_with(False, "Нет сырых снимков для обработки. Загрузите их с устройства.")

def test_run_images_different_sizes(worker):
    """Тестирует случай, когда изображения имеют разные размеры."""
    raw_images_mocks = [
        create_mock_raw_image(wavelength=500),
        create_mock_raw_image(wavelength=600)
    ]
    worker.mocks['db_session'].query(RawImage).filter_by.return_value.options.return_value.all.return_value = raw_images_mocks
    
    # Настройка разных размеров для изображений
    img_mock1 = MagicMock()
    img_mock1.size = (10, 10)
    img_mock1.convert.return_value = img_mock1
    
    img_mock2 = MagicMock()
    img_mock2.size = (12, 12) # Другой размер
    img_mock2.convert.return_value = img_mock2
    
    worker.mocks['Image_open'].side_effect = [img_mock1, img_mock2]
    
    worker.run()
    
    worker.finished.emit.assert_called_once_with(False, "Все снимки должны быть одного размера!")

def test_run_no_chromophores(worker):
    """Тестирует случай, когда в БД нет хромофоров."""
    raw_images_mocks = [create_mock_raw_image(wavelength=500)]
    worker.mocks['db_session'].query(RawImage).filter_by.return_value.options.return_value.all.return_value = raw_images_mocks
    worker.mocks['db_session'].query(Chromophore).order_by.return_value.all.return_value = [] # Нет хромофоров
    
    # Мок для Image.open().convert("L") и np.array()
    # np.array(Image.open(ri.file_path).convert("L"), dtype=np.float32)
    # Должен вернуть 2D numpy массив
    worker.mocks['Image_open'].return_value.convert.return_value = np.zeros((10,10), dtype=np.uint8)


    worker.run()
    
    worker.finished.emit.assert_called_once_with(False, "В базе данных отсутствуют хромофоры.")


# --- Тесты для THb ---
@pytest.mark.parametrize("hbo2_conc, hb_conc, expected_thb_factor, hbo2_present, hb_present, other_chrom_present, warning_msg_part", [
    # Случай 1: HbO2 и Hb присутствуют
    (0.5, 0.3, 0.8, True, True, False, "Информация: THb = |HbO2| + |Hb|."), 
    # Случай 2: Только HbO2 присутствует
    (0.5, 0.0, 0.5, True, False, False, "Предупреждение: Хромофор Hb не найден."),
    # Случай 3: Только Hb присутствует
    (0.0, 0.3, 0.3, False, True, False, "Предупреждение: Хромофор HbO2 не найден."),
    # Случай 4: Ни HbO2, ни Hb, но есть другой (первый в списке)
    (0.0, 0.0, 0.7, False, False, True, "Предупреждение: Хромофоры Hb и HbO2 не найдены. THb основан на первом доступном хромофоре: Other."),
])
def test_thb_calculation_scenarios(worker, hbo2_conc, hb_conc, expected_thb_factor, hbo2_present, hb_present, other_chrom_present, warning_msg_part):
    """
    Тестирует расчет THb для различных сценариев наличия HbO2 и Hb.
    """
    # --- Настройка моков ---
    mock_chromophores = []
    chrom_idx_counter = 0
    if hbo2_present:
        mock_chromophores.append(create_mock_chromophore(id_val=chrom_idx_counter, symbol_val="HbO2"))
        chrom_idx_counter +=1
    if hb_present:
        mock_chromophores.append(create_mock_chromophore(id_val=chrom_idx_counter, symbol_val="Hb"))
        chrom_idx_counter +=1
    if other_chrom_present: # "Other" будет первым, если HbO2 и Hb отсутствуют
        mock_chromophores.insert(0, create_mock_chromophore(id_val=chrom_idx_counter, symbol_val="Other"))
        chrom_idx_counter +=1
    
    # Если список хромофоров пуст (не должно быть по логике теста, но для полноты)
    if not mock_chromophores:
        mock_chromophores.append(create_mock_chromophore(id_val=0, symbol_val="Fallback"))


    worker.mocks['db_session'].query(Chromophore).order_by.return_value.all.return_value = mock_chromophores
    
    # Мок для concentration_maps
    # (n_chroms, H, W)
    num_chroms_in_map = len(mock_chromophores)
    
    # Создаем concentration_maps: Каждая карта - это просто число * np.ones((10,10))
    # Важно, чтобы порядок соответствовал mock_chromophores
    concentration_maps_data = []
    current_map_idx = 0
    # Логика присвоения концентраций должна соответствовать порядку в mock_chromophores
    if other_chrom_present and not (hbo2_present or hb_present): # "Other" - первый и единственный значимый
        concentration_maps_data.append(0.7 * np.ones((10,10), dtype=np.float32)) # Концентрация для "Other"
        current_map_idx +=1
    if hbo2_present:
        concentration_maps_data.append(hbo2_conc * np.ones((10,10), dtype=np.float32))
        current_map_idx +=1
    if hb_present:
        concentration_maps_data.append(hb_conc * np.ones((10,10), dtype=np.float32))
        current_map_idx +=1
    
    # Если из-за логики выше карт не добавилось, а хромофоры есть (например, Fallback)
    while len(concentration_maps_data) < num_chroms_in_map:
        concentration_maps_data.append(0.01 * np.ones((10,10), dtype=np.float32)) # Небольшое значение по умолчанию

    # Мокируем np.linalg.lstsq так, чтобы он возвращал срезы из этих concentration_maps
    # lstsq вызывается для каждого пикселя (H*W раз).
    # Он должен вернуть вектор концентраций для этого пикселя.
    # Мы сделаем проще: lstsq будет возвращать один и тот же вектор (первый "столбец" из concentration_maps_data)
    
    # (n_chroms, H, W) -> (H, W, n_chroms) -> reshape to (H*W, n_chroms)
    # Затем lstsq_side_effect будет выдавать по одной строке
    pixel_concentration_vectors = []
    if concentration_maps_data: # Если есть данные для карт
        stacked_maps = np.stack(concentration_maps_data, axis=0) # (n_chroms, H, W)
        for y_idx in range(10): # H
            for x_idx in range(10): # W
                pixel_concentration_vectors.append(stacked_maps[:, y_idx, x_idx])
    else: # Если concentration_maps_data пуст (например, нет хромофоров)
        # lstsq не должен вызываться, если нет хромофоров, но на всякий случай
        pixel_concentration_vectors.append(np.array([]))


    worker.mocks['np_linalg_lstsq'].side_effect = pixel_concentration_vectors

    # Мок для raw_images и overlap_matrix (минимально необходимые)
    mock_raw_img = create_mock_raw_image(wavelength=500, spectrum_id=1)
    worker.mocks['db_session'].query(RawImage).filter_by.return_value.options.return_value.all.return_value = [mock_raw_img]
    
    # overlap_matrix (n_spectra, n_chroms)
    # Для этого теста нам не важны значения в overlap_matrix, т.к. мы мокируем выход lstsq
    # Но она должна быть создана с правильным числом хромофоров
    overlap_coeffs = []
    for i, chrom in enumerate(mock_chromophores):
        overlap_coeffs.append(create_mock_overlap_coefficient(1, chrom.id, 0.1))
    
    # Фильтр для коэффициентов перекрытия
    def mock_overlap_query_filter_by(spectrum_id, chromophore_id):
        mock_query = MagicMock()
        found = [c for c in overlap_coeffs if c.spectrum_id == spectrum_id and c.chromophore_id == chromophore_id]
        mock_query.first.return_value = found[0] if found else None
        return mock_query

    worker.mocks['db_session'].query(OverlapCoefficient).filter_by.side_effect = mock_overlap_query_filter_by
    
    # Мок для Image.open().convert("L")
    # np.array(Image.open(ri.file_path).convert("L"), dtype=np.float32)
    # Должен вернуть 2D numpy массив (10x10)
    worker.mocks['Image_open'].return_value.convert.return_value = np.ones((10,10), dtype=np.uint8) * 128 # Средняя интенсивность

    # --- Запуск метода ---
    # Мокируем сохранение изображений и Result, чтобы не выполнять лишние шаги
    worker.mocks['db_session'].query(Result).filter_by.return_value.first.return_value = None # Нет старых результатов
    worker.mocks['db_session'].query(ReconstructedImage).filter_by.return_value.all.return_value = [] # Нет старых реконструированных

    worker.run()

    # --- Проверки ---
    # 1. Проверка сообщения о прогрессе (содержит ли оно ожидаемую часть)
    # Собираем все вызовы worker.progress.emit(*args)
    progress_calls = [args[0] for args, kwargs in worker.progress.emit.call_args_list]
    assert any(warning_msg_part in call_text for call_text in progress_calls), \
        f"Ожидаемое сообщение '{warning_msg_part}' не найдено в логах прогресса: {progress_calls}"

    # 2. Проверка, что finished был вызван с успехом (True)
    # worker.finished.emit.assert_called_once() # Нельзя, т.к. может быть вызван с ошибкой раньше
    assert worker.finished.emit.call_args is not None, "finished сигнал не был вызван"
    assert worker.finished.emit.call_args[0][0] is True, \
        f"Обработка не завершилась успешно: {worker.finished.emit.call_args[0][1]}"

    # 3. Проверка thb_map (если обработка дошла до этого шага)
    # thb_map передается в gaussian, затем результат нормализуется и передается в cv2.threshold
    # Мы можем проверить аргумент, переданный в worker.mocks['skimage_gaussian']
    
    # Если worker.run() завершился успешно (не было return раньше из-за ошибки)
    if worker.finished.emit.call_args[0][0] is True:
        assert worker.mocks['skimage_gaussian'].call_count > 0, "skimage.filters.gaussian не был вызван"
        called_with_thb_map = worker.mocks['skimage_gaussian'].call_args[0][0]
        
        expected_thb_map = np.ones((10,10), dtype=np.float32) * expected_thb_factor
        np.testing.assert_allclose(called_with_thb_map, expected_thb_map, rtol=1e-5,
                                   err_msg="Рассчитанная thb_map не соответствует ожидаемой.")

# --- Тесты для Сегментации ---
def test_segmentation_logic(worker):
    """
    Тестирует логику сегментации: Гауссово размытие + Otsu от OpenCV.
    """
    # --- Настройка моков ---
    # 1. Создаем простую thb_map для теста
    # Пусть это будет карта 10x10, где левая половина имеет значения ~50, а правая ~100
    # Мы ожидаем, что порог Отсу будет где-то между 50 и 100.
    thb_map_data = np.zeros((10, 10), dtype=np.float32)
    thb_map_data[:, :5] = 50.0
    thb_map_data[:, 5:] = 100.0
    
    # 2. Мокируем результаты предыдущих шагов, чтобы worker.run() мог дойти до сегментации
    #   - chromophores (хотя бы один)
    #   - concentration_maps (чтобы thb_map можно было "рассчитать")
    #   - raw_images
    #   - overlap_coefficients
    
    mock_chrom = create_mock_chromophore(id_val=1, symbol_val="HbO2") # Один хромофор для простоты
    worker.mocks['db_session'].query(Chromophore).order_by.return_value.all.return_value = [mock_chrom]
    
    # np.linalg.lstsq будет возвращать значения, которые дадут нам нашу thb_map_data
    # Если у нас один хромофор, то lstsq должен вернуть (1, H, W) массив -> (H*W, 1) векторов
    pixel_concentration_vectors = []
    for y_idx in range(10):
        for x_idx in range(10):
            pixel_concentration_vectors.append(np.array([thb_map_data[y_idx, x_idx]])) # Концентрация = значение thb_map
    worker.mocks['np_linalg_lstsq'].side_effect = pixel_concentration_vectors

    mock_raw_img = create_mock_raw_image(wavelength=500, spectrum_id=1)
    worker.mocks['db_session'].query(RawImage).filter_by.return_value.options.return_value.all.return_value = [mock_raw_img]
    mock_overlap_coeff = create_mock_overlap_coefficient(1, mock_chrom.id, 1.0) # Коэфф. = 1 для простоты
    worker.mocks['db_session'].query(OverlapCoefficient).filter_by.return_value.first.return_value = mock_overlap_coeff
    worker.mocks['Image_open'].return_value.convert.return_value = np.ones((10,10), dtype=np.uint8) * 128

    # 3. Настройка моков для самой сегментации
    #   - skimage.filters.gaussian: пусть он просто возвращает исходную карту без изменений для этого теста,
    #     чтобы мы могли точно предсказать вход для cv2.threshold.
    worker.mocks['skimage_gaussian'].side_effect = lambda image, sigma, preserve_range: image 

    #   - cv2.threshold: мы зададим, какой порог он "найдет" и какую маску вернет.
    #     Для thb_map_data (50 и 100), Отсу должен дать порог около 75.
    #     Пусть cv2.threshold вернет порог 75.
    #     Тогда все, что >= 75 (т.е. значения 100) будет 255 (lesion), остальное 0 (skin).
    expected_otsu_thresh_val = 75
    expected_binary_img = np.zeros((10, 10), dtype=np.uint8)
    expected_binary_img[:, 5:] = 255 # Правая половина, где было 100
    worker.mocks['cv2_threshold'].return_value = (expected_otsu_thresh_val, expected_binary_img)

    # Мокируем Result и ReconstructedImage для предотвращения ошибок в конце run
    worker.mocks['db_session'].query(Result).filter_by.return_value.first.return_value = None
    worker.mocks['db_session'].query(ReconstructedImage).filter_by.return_value.all.return_value = []


    # --- Запуск метода ---
    worker.run()

    # --- Проверки ---
    # 1. Проверить, что gaussian был вызван с thb_map_data
    worker.mocks['skimage_gaussian'].assert_called_once()
    call_args_gaussian = worker.mocks['skimage_gaussian'].call_args[0][0]
    np.testing.assert_allclose(call_args_gaussian, thb_map_data, rtol=1e-5,
                               err_msg="skimage.gaussian был вызван с неожиданной картой THb.")

    # 2. Проверить, что cv2.threshold был вызван с нормализованной картой после Гаусса
    #    Вход для cv2.threshold - это thb_norm_uint8
    #    thb_blurred (выход Гаусса) = thb_map_data (из-за нашего мока Гаусса)
    #    min_val_blurred = 50, max_val_blurred = 100, range_val_blurred = 50
    #    thb_norm_uint8[:, :5] = (50-50)/50 * 255 = 0
    #    thb_norm_uint8[:, 5:] = (100-50)/50 * 255 = 255
    expected_input_to_cv2_thresh = np.zeros((10,10), dtype=np.uint8)
    expected_input_to_cv2_thresh[:, 5:] = 255
    
    worker.mocks['cv2_threshold'].assert_called_once()
    call_args_cv2_thresh = worker.mocks['cv2_threshold'].call_args[0][0]
    np.testing.assert_array_equal(call_args_cv2_thresh, expected_input_to_cv2_thresh,
                                  err_msg="cv2.threshold был вызван с неожиданной нормализованной картой.")

    # 3. Проверить, что S-коэффициент рассчитался (это будет использовать mask_lesion/mask_skin)
    #    Мы знаем, что finished должен быть вызван с True, если все прошло хорошо
    assert worker.finished.emit.call_args is not None, "finished сигнал не был вызван"
    assert worker.finished.emit.call_args[0][0] is True, \
        f"Обработка не завершилась успешно: {worker.finished.emit.call_args[0][1]}"

    # 4. Косвенно, mask_lesion и mask_skin используются для расчета статистик,
    #    которые затем передаются в results_data в finished.emit.
    #    mask_lesion должна быть True там, где expected_binary_img == 255
    #    mask_skin должна быть True там, где expected_binary_img != 255
    #    mean_lesion_thb (на основе thb_map_data): np.mean(thb_map_data[:, 5:]) = 100
    #    mean_skin_thb (на основе thb_map_data): np.mean(thb_map_data[:, :5]) = 50
    results_data = worker.finished.emit.call_args[0][1]
    assert results_data['mean_lesion_thb'] == pytest.approx(100.0)
    assert results_data['mean_skin_thb'] == pytest.approx(50.0)


# --- Тесты для S-коэффициента ---
@pytest.mark.parametrize("mean_lesion, mean_skin, expected_s_coeff", [
    (100.0, 50.0, 2.0),      # Нормальный случай
    (100.0, 0.0, 0.0),       # Деление на ноль (mean_skin_thb = 0)
    (100.0, 1e-7, 0.0),      # Деление на очень малое число (близкое к нулю по условию > 1e-6)
    (0.0, 50.0, 0.0),        # Очаг с нулевым THb
    (50.0, 100.0, 0.5),      # S-коэффициент < 1
])
def test_s_coefficient_calculation(worker, mean_lesion, mean_skin, expected_s_coeff):
    """
    Тестирует расчет S-коэффициента для различных входных средних значений.
    """
    # --- Настройка моков ---
    # 1. Создаем thb_map и маски, которые дадут нужные средние значения
    #    Проще всего мокировать np.nanmean напрямую для этого теста,
    #    чтобы не возиться с созданием сложных thb_map и масок.
    
    #    Первый вызов np.nanmean - для mean_lesion_thb, второй - для mean_skin_thb
    worker.mocks['np_nanmean_patch'] = patch('numpy.nanmean', side_effect=[mean_lesion, mean_skin]).start()
    # Также нужно мокировать np.any, чтобы он возвращал True (маски не пустые)
    worker.mocks['np_any_patch'] = patch('numpy.any', return_value=True).start()

    # 2. Мокируем остальные части, чтобы worker.run() дошел до расчета S-коэффициента
    mock_chrom = create_mock_chromophore(id_val=1, symbol_val="HbO2")
    worker.mocks['db_session'].query(Chromophore).order_by.return_value.all.return_value = [mock_chrom]
    # lstsq возвращает что-то, что даст непустую thb_map
    worker.mocks['np_linalg_lstsq'].side_effect = [[0.5]] * 100 # 10x10 пикселей, концентрация 0.5
    mock_raw_img = create_mock_raw_image(wavelength=500, spectrum_id=1)
    worker.mocks['db_session'].query(RawImage).filter_by.return_value.options.return_value.all.return_value = [mock_raw_img]
    mock_overlap_coeff = create_mock_overlap_coefficient(1, mock_chrom.id, 1.0)
    worker.mocks['db_session'].query(OverlapCoefficient).filter_by.return_value.first.return_value = mock_overlap_coeff
    worker.mocks['Image_open'].return_value.convert.return_value = np.ones((10,10), dtype=np.uint8) * 128
    # Gaussian и cv2.threshold тоже должны что-то вернуть
    worker.mocks['skimage_gaussian'].side_effect = lambda x, sigma, preserve_range: x
    worker.mocks['cv2_threshold'].return_value = (128, np.ones((10,10), dtype=np.uint8)*128) # Некая бинарная маска
    worker.mocks['db_session'].query(Result).filter_by.return_value.first.return_value = None
    worker.mocks['db_session'].query(ReconstructedImage).filter_by.return_value.all.return_value = []

    # --- Запуск метода ---
    worker.run()

    # --- Проверки ---
    assert worker.finished.emit.call_args is not None, "finished сигнал не был вызван"
    assert worker.finished.emit.call_args[0][0] is True, \
        f"Обработка не завершилась успешно: {worker.finished.emit.call_args[0][1]}"
    
    results_data = worker.finished.emit.call_args[0][1]
    assert results_data['s_coefficient'] == pytest.approx(expected_s_coeff)

    # Останавливаем патчи, запущенные вручную
    worker.mocks['np_nanmean_patch'].stop()
    worker.mocks['np_any_patch'].stop()

# --- Тесты для обработки ошибок в сегментации ---
@pytest.mark.parametrize("cv2_fails, skimage_fails, expected_threshold_source_message_part, expected_final_threshold", [
    (True, False, "Ошибка Otsu (cv2):.*Попытка с skimage.filters.threshold_otsu", 75), # cv2 падает, skimage работает
    (True, True, "Ошибка Otsu (skimage):.*Используется порог 128", 128), # Оба падают, используется дефолт
])
def test_segmentation_error_handling(worker, cv2_fails, skimage_fails, expected_threshold_source_message_part, expected_final_threshold):
    """
    Тестирует обработку ошибок при вызове cv2.threshold и skimage.filters.threshold_otsu.
    """
    # --- Настройка моков ---
    thb_map_data = np.zeros((10, 10), dtype=np.float32) # Простая карта
    thb_map_data[:, :5] = 50.0
    thb_map_data[:, 5:] = 100.0

    mock_chrom = create_mock_chromophore(id_val=1, symbol_val="HbO2")
    worker.mocks['db_session'].query(Chromophore).order_by.return_value.all.return_value = [mock_chrom]
    pixel_concentration_vectors = [[thb_map_data[y,x]] for y in range(10) for x in range(10)]
    worker.mocks['np_linalg_lstsq'].side_effect = pixel_concentration_vectors
    mock_raw_img = create_mock_raw_image(wavelength=500, spectrum_id=1)
    worker.mocks['db_session'].query(RawImage).filter_by.return_value.options.return_value.all.return_value = [mock_raw_img]
    mock_overlap_coeff = create_mock_overlap_coefficient(1, mock_chrom.id, 1.0)
    worker.mocks['db_session'].query(OverlapCoefficient).filter_by.return_value.first.return_value = mock_overlap_coeff
    worker.mocks['Image_open'].return_value.convert.return_value = np.ones((10,10), dtype=np.uint8) * 128
    worker.mocks['skimage_gaussian'].side_effect = lambda image, sigma, preserve_range: image 

    if cv2_fails:
        worker.mocks['cv2_threshold'].side_effect = Exception("CV2 Otsu failed")
        if skimage_fails:
            worker.mocks['skimage_threshold_otsu'].side_effect = Exception("Skimage Otsu failed")
        else:
            # skimage работает и возвращает порог 75
            worker.mocks['skimage_threshold_otsu'].return_value = 75 
    else:
        # cv2 работает (этот случай не должен попадать сюда из-за parametrize, но для полноты)
        worker.mocks['cv2_threshold'].return_value = (75, np.zeros((10,10),dtype=np.uint8))


    worker.mocks['db_session'].query(Result).filter_by.return_value.first.return_value = None
    worker.mocks['db_session'].query(ReconstructedImage).filter_by.return_value.all.return_value = []
    
    # --- Запуск ---
    worker.run()

    # --- Проверки ---
    progress_calls = [args[0] for args, kwargs in worker.progress.emit.call_args_list]
    assert any(expected_threshold_source_message_part in call_text for call_text in progress_calls), \
        f"Ожидаемое сообщение '{expected_threshold_source_message_part}' не найдено в логах прогресса: {progress_calls}"

    # Проверяем, что финальное сообщение о сегментации содержит ожидаемый порог
    final_segmentation_message = next(p for p in progress_calls if "Сегментация завершена. Порог Otsu:" in p)
    assert f"Порог Otsu: {expected_final_threshold:.2f}" in final_segmentation_message

    # Проверяем, что обработка завершилась успешно
    assert worker.finished.emit.call_args is not None, "finished сигнал не был вызван"
    assert worker.finished.emit.call_args[0][0] is True, \
        f"Обработка не завершилась успешно: {worker.finished.emit.call_args[0][1]}"


# --- Тесты для сохранения результатов ---
def test_save_results_logic(worker):
    """
    Тестирует логику сохранения результатов: Result, ReconstructedImage, удаление старых данных.
    """
    # --- Настройка моков ---
    # Базовые моки для прохождения до этапа сохранения
    thb_map_data = np.ones((10,10), dtype=np.float32) * 70.0 # Простая thb_map
    mock_chrom1 = create_mock_chromophore(id_val=1, symbol_val="HbO2")
    mock_chrom2 = create_mock_chromophore(id_val=2, symbol_val="Hb")
    mock_chromophores = [mock_chrom1, mock_chrom2]
    worker.mocks['db_session'].query(Chromophore).order_by.return_value.all.return_value = mock_chromophores
    
    # np.linalg.lstsq должен вернуть 2 карты концентраций
    # (2, 10, 10) -> (100, 2)
    conc_map1_data = np.ones((10,10), dtype=np.float32) * 0.4 # для HbO2
    conc_map2_data = np.ones((10,10), dtype=np.float32) * 0.3 # для Hb
    pixel_concentration_vectors = []
    for y_idx in range(10):
        for x_idx in range(10):
            pixel_concentration_vectors.append(np.array([conc_map1_data[y_idx,x_idx], conc_map2_data[y_idx,x_idx]]))
    worker.mocks['np_linalg_lstsq'].side_effect = pixel_concentration_vectors
    
    mock_raw_img = create_mock_raw_image(wavelength=500, spectrum_id=1, file_path="/fake/dir/raw_img.png")
    worker.mocks['db_session'].query(RawImage).filter_by.return_value.options.return_value.all.return_value = [mock_raw_img]
    # Коэффициенты перекрытия
    overlap_coeffs_data = [
        create_mock_overlap_coefficient(1, 1, 0.1), create_mock_overlap_coefficient(1, 2, 0.2)
    ]
    def mock_overlap_query_filter_by_side_effect(spectrum_id, chromophore_id):
        mock_q = MagicMock()
        found = [c for c in overlap_coeffs_data if c.spectrum_id == spectrum_id and c.chromophore_id == chromophore_id]
        mock_q.first.return_value = found[0] if found else None
        return mock_q
    worker.mocks['db_session'].query(OverlapCoefficient).filter_by.side_effect = mock_overlap_query_filter_by_side_effect

    worker.mocks['Image_open'].return_value.convert.return_value = np.ones((10,10), dtype=np.uint8) * 128
    worker.mocks['skimage_gaussian'].side_effect = lambda image, sigma, preserve_range: image 
    worker.mocks['cv2_threshold'].return_value = (128, np.ones((10,10), dtype=np.uint8)) # Некая маска

    # Моки для os.path.join - важно, чтобы пути были предсказуемы
    # base_photo_dir = os.path.dirname(raw_images[0].file_path) -> /fake/dir
    # processed_dir = os.path.join(base_photo_dir, f"processed_{self.session_id}") -> /fake/dir/processed_test_session_id
    # thb_img_path = os.path.join(processed_dir, "thb_map.png") -> /fake/dir/processed_test_session_id/thb_map.png
    # mask_img_path = os.path.join(processed_dir, "mask_otsu.png")
    # img_path = os.path.join(processed_dir, f"{chrom.symbol.replace('/', '_')}.png")
    
    expected_processed_dir = "/fake/dir/processed_test_session_id"
    expected_thb_path = "/fake/dir/processed_test_session_id/thb_map.png"
    expected_mask_path = "/fake/dir/processed_test_session_id/mask_otsu.png"
    expected_hbo2_path = "/fake/dir/processed_test_session_id/HbO2.png"
    expected_hb_path = "/fake/dir/processed_test_session_id/Hb.png"

    def os_path_join_side_effect(*args):
        # Простая реализация, чтобы избежать слишком сложного мокирования os.path
        return "/".join(args)

    worker.mocks['os_path_join'].side_effect = os_path_join_side_effect
    worker.mocks['os_path_dirname'].return_value = "/fake/dir" # Уже есть в base_mocks, но для ясности

    # Моки для удаления старых данных
    mock_old_result = MagicMock(spec=Result)
    worker.mocks['db_session'].query(Result).filter_by.return_value.first.return_value = mock_old_result
    
    mock_old_rec_img1 = MagicMock(spec=ReconstructedImage, file_path="/fake/dir/old_hbo2.png")
    mock_old_rec_img2 = MagicMock(spec=ReconstructedImage, file_path="/fake/dir/old_hb.png")
    worker.mocks['db_session'].query(ReconstructedImage).filter_by.return_value.all.return_value = [mock_old_rec_img1, mock_old_rec_img2]
    worker.mocks['os_path_isfile'].side_effect = lambda path: path in ["/fake/dir/old_hbo2.png", "/fake/dir/old_hb.png"]


    # --- Запуск ---
    worker.run()

    # --- Проверки ---
    # 1. Удаление старого Result
    worker.mocks['db_session'].delete.assert_any_call(mock_old_result)

    # 2. Удаление старых ReconstructedImage и их файлов
    worker.mocks['os_remove'].assert_any_call("/fake/dir/old_hbo2.png")
    worker.mocks['os_remove'].assert_any_call("/fake/dir/old_hb.png")
    worker.mocks['db_session'].delete.assert_any_call(mock_old_rec_img1)
    worker.mocks['db_session'].delete.assert_any_call(mock_old_rec_img2)
    
    # 3. Проверка вызовов os.makedirs
    worker.mocks['os_makedirs'].assert_called_once_with(expected_processed_dir, exist_ok=True)

    # 4. Проверка сохранения изображений (THb, маска, карты хромофоров)
    #    Image.fromarray(...).save(path)
    #    Мы можем проверить пути, с которыми вызывался save()
    #    worker.mocks['Image_fromarray'].return_value.save.call_args_list дает список вызовов
    #    Первый вызов save - для thb_map.png (после нормализации оригинальной thb_map)
    #    Второй вызов save - для mask_otsu.png (mask_lesion * 255)
    #    Третий вызов save - для HbO2.png
    #    Четвертый вызов save - для Hb.png
    save_calls = [call_args[0][0] for call_args in worker.mocks['Image_fromarray'].return_value.save.call_args_list]
    
    assert expected_thb_path in save_calls
    assert expected_mask_path in save_calls
    assert expected_hbo2_path in save_calls
    assert expected_hb_path in save_calls
    
    # 5. Проверка добавления нового Result в БД
    #    result_obj = Result(...)
    #    db.add(result_obj)
    #    Ищем вызов db.add() с объектом Result
    added_to_db = [call_arg[0][0] for call_arg in worker.mocks['db_session'].add.call_args_list]
    new_result_obj = next(obj for obj in added_to_db if isinstance(obj, Result))
    assert new_result_obj.session_id == "test_session_id"
    assert new_result_obj.thb_path == expected_thb_path
    assert new_result_obj.contour_path == expected_mask_path
    
    # Для s_coefficient, mean_lesion_thb, mean_skin_thb - мокируем nanmean и any
    # Это значение S-коэффициента будет проверено ниже
    expected_s_coeff_in_save_test = 1.5 
    expected_mean_lesion_thb_in_save_test = 0.6
    expected_mean_skin_thb_in_save_test = 0.4

    assert new_result_obj.s_coefficient == pytest.approx(expected_s_coeff_in_save_test)
    assert new_result_obj.mean_lesion_thb == pytest.approx(expected_mean_lesion_thb_in_save_test)
    assert new_result_obj.mean_skin_thb == pytest.approx(expected_mean_skin_thb_in_save_test)
    # Проверка новых полей для параметров сегментации
    assert new_result_obj.segmentation_gaussian_sigma == pytest.approx(1.0) # Как установлено в process_worker
    assert new_result_obj.segmentation_otsu_threshold == pytest.approx(128.0) # Как возвращает мок cv2.threshold в этом тесте

    # 6. Проверка добавления новых ReconstructedImage в БД
    new_rec_imgs = [obj for obj in added_to_db if isinstance(obj, ReconstructedImage)]
    assert len(new_rec_imgs) == 2
    
    rec_hbo2 = next(img for img in new_rec_imgs if img.chromophore_id == mock_chrom1.id)
    rec_hb = next(img for img in new_rec_imgs if img.chromophore_id == mock_chrom2.id)
    
    assert rec_hbo2.file_path == expected_hbo2_path
    assert rec_hb.file_path == expected_hb_path
    assert rec_hbo2.session_id == "test_session_id"

    # 7. Проверка вызова db.commit()
    worker.mocks['db_session'].commit.assert_called_once()

    # 8. Проверка данных в finished.emit
    assert worker.finished.emit.call_args is not None, "finished сигнал не был вызван"
    assert worker.finished.emit.call_args[0][0] is True
    results_data = worker.finished.emit.call_args[0][1]
    assert results_data['thb_map_path'] == expected_thb_path
    assert results_data['mask_path'] == expected_mask_path
    assert results_data['s_coefficient'] == pytest.approx(expected_s_coeff_in_save_test)
    assert results_data['mean_lesion_thb'] == pytest.approx(expected_mean_lesion_thb_in_save_test)
    assert results_data['mean_skin_thb'] == pytest.approx(expected_mean_skin_thb_in_save_test)
    assert results_data['chromophore_images'] == {
        "HbO2": expected_hbo2_path,
        "Hb": expected_hb_path
    }
    
    # Останавливаем патчи, запущенные для этого теста
    np_nanmean_patch.stop()
    np_any_patch.stop()

if __name__ == "__main__":
    pytest.main()
"""
