from collections import Counter
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_HALF_UP

from calculate.models import (
    Beams,
    Color,
    Glass,
    GlukharGlass,
    GlukharWood,
    Hardware,
    PortalWood,
    Scheme,
    Work,
)

ZERO = Decimal("0")
TWO = Decimal("2")
HUNDRED = Decimal("100")
THOUSAND = Decimal("1000")
MILLION = Decimal("1000000")
LIMIT_3000 = Decimal("3000")
TEN = Decimal("10")
NINE = Decimal("9")
ONE_HUNDRED_TEN = Decimal("110")
FIFTY_FIVE = Decimal("55")
ONE_HUNDRED_SIXTY = Decimal("160")
FOURTEEN_THOUSAND = Decimal("14000")

GLASS_HEIGHT_DOOR_SUB = Decimal("202")
GLASS_HEIGHT_SASH_SUB = Decimal("46")
GLUKHAR_GLASS_SUB = Decimal("78")
WEIGHT_GLASS_CONST = Decimal("55")

BEAM_LIST_FOR_WORK = [
    "1К",
    "2",
    "3К",
    "4К",
    "5К",
    "6К",
    "7К",
    "8К",
    "9С",
    "10К",
    "11К",
    "14С",
]


def to_decimal(value, default="0") -> Decimal:
    if isinstance(value, Decimal):
        return value

    if value is None:
        return Decimal(default)

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def _quantum(places: int) -> Decimal:
    return Decimal(1).scaleb(-int(places))


def dec_round(value, places: int = 2) -> Decimal:
    value = to_decimal(value)
    if places is None:
        return value

    return value.quantize(_quantum(places), rounding=ROUND_HALF_UP)


def dec_ceil(value, places: int | None = None) -> Decimal:
    value = to_decimal(value)
    if places is None:
        return value.to_integral_value(rounding=ROUND_CEILING)

    return value.quantize(_quantum(places), rounding=ROUND_CEILING)


def money(value) -> Decimal:
    return dec_round(value, 2)


def as_number(value):
    value = to_decimal(value)
    integral = value.to_integral_value()
    if value == integral:
        return int(integral)

    return value


def _first_two(values) -> list[Decimal]:
    result = [to_decimal(value) for value in values]
    while len(result) < 2:
        result.append(ZERO)

    return result[:2]


def _contains_dash(value) -> bool:
    if not isinstance(value, dict):
        return False

    return "-" in value.keys() or "-" in value.values()


def get_price(beam_name: str) -> Decimal:
    return to_decimal(Beams.objects.get(name=beam_name).price)


def get_length(beam_name: str) -> Decimal:
    return to_decimal(Beams.objects.get(name=beam_name).length) * THOUSAND


def get_door_amount(scheme_name: str) -> int:
    return int(to_decimal(Scheme.objects.get(name=scheme_name).door))


def get_fixed_sash_amount(scheme_name: str) -> int:
    return int(to_decimal(Scheme.objects.get(name=scheme_name).fixed_sash))


def get_rails_amount(scheme_name: str) -> int:
    return int(to_decimal(Scheme.objects.get(name=scheme_name).rail_amour))


def get_coverage_rate_doors(color_prefix: str) -> list[Decimal]:
    return _first_two(
        Color.objects.filter(name__startswith=color_prefix)
        .order_by("id")
        .values_list("coverage_rate_doors", flat=True)[:2],
    )


def get_price_color(color_prefix: str) -> list[Decimal]:
    return _first_two(
        Color.objects.filter(name__startswith=color_prefix)
        .order_by("id")
        .values_list("price", flat=True)[:2],
    )


def get_coverage_rate_sashes(color_prefix: str) -> list[Decimal]:
    return _first_two(
        Color.objects.filter(name__startswith=color_prefix)
        .order_by("id")
        .values_list("coverage_rate_sash", flat=True)[:2],
    )


def get_sub_num(door_type: str, scheme_name: str) -> Decimal:
    scheme = Scheme.objects.get(name=scheme_name)
    value = scheme.door_sub if door_type == "door" else scheme.sash_sub
    return to_decimal(value)


def get_glass_price(glass_type: str) -> Decimal:
    return to_decimal(Glass.objects.get(name=glass_type).price)


def get_salary(beam_name: str, worker: str) -> Decimal:
    work = Work.objects.get(beam=beam_name)
    if worker == "carpenter":
        return to_decimal(work.carpenter)

    return to_decimal(work.painter)


def get_price_glukhar(wood_type: str) -> Decimal:
    return to_decimal(GlukharWood.objects.get(name=wood_type).price)


def get_price_glass_glukhar_on_area(area) -> Decimal:
    area = to_decimal(area)
    if area >= TEN:
        area = NINE

    instance = GlukharGlass.objects.filter(
        min_area__lte=area,
        max_area__gt=area,
    ).first()

    if not instance:
        return ZERO

    return to_decimal(instance.price)


def mul_dict(dictionary: dict) -> Decimal:
    total = ZERO

    if not isinstance(dictionary, dict):
        return total

    for key, value in dictionary.items():
        if key == "-" or value == "-":
            continue

        total += to_decimal(key) * to_decimal(value)

    return total


def get_door_area(portal_width, portal_height, scheme_name: str) -> Decimal:
    door_count = get_door_amount(scheme_name)
    fixed_sash_count = get_fixed_sash_amount(scheme_name)
    total_parts = door_count + fixed_sash_count

    if total_parts == 0:
        return ZERO

    width = dec_ceil(to_decimal(portal_width) / to_decimal(total_parts))
    return (width * to_decimal(portal_height)) / MILLION


def get_perimeter(width, height) -> Decimal:
    return (TWO * (to_decimal(width) + to_decimal(height))) / THOUSAND


def find_multiple_perimeter(perimeter, n=6) -> Decimal:
    n_dec = to_decimal(n)
    if n_dec == ZERO:
        return to_decimal(perimeter)

    return dec_ceil(to_decimal(perimeter) / n_dec) * n_dec


def count_frequencies(lst) -> dict:
    return dict(Counter(lst))


def process_list(lst) -> list:
    sorted_list = sorted((to_decimal(item) for item in lst), reverse=True)
    result = []
    used = [False] * len(sorted_list)

    for i in range(len(sorted_list)):
        if used[i]:
            continue

        current = sorted_list[i]

        if current == LIMIT_3000:
            result.append(LIMIT_3000)
            used[i] = True
            continue

        combination = [current]
        total = current
        used[i] = True

        for j in range(i + 1, len(sorted_list)):
            if not used[j] and total + sorted_list[j] <= LIMIT_3000:
                total += sorted_list[j]
                combination.append(sorted_list[j])
                used[j] = True

        if len(combination) > 1:
            result.append(LIMIT_3000)
        else:
            result.append(current)

    return sorted(result, key=to_decimal)


def calculate_parts(total_length, part_length=3000) -> list:
    total_length = to_decimal(total_length)
    part_length = to_decimal(part_length)
    parts = []

    while total_length >= part_length:
        parts.append(as_number(part_length))
        total_length -= part_length

    if total_length > ZERO:
        parts.append(as_number(total_length))

    return parts


def count_bars(width, height, bar_length=6) -> int:
    perimeter = find_multiple_perimeter(get_perimeter(width, height))
    bar_length_dec = to_decimal(bar_length)

    if bar_length_dec == ZERO:
        return 0

    return int(dec_ceil(perimeter / bar_length_dec))


def amount_k1(portal_width, portal_height):
    width = to_decimal(portal_width)
    height = as_number(portal_height)

    amount_h = [height, height]

    if width >= LIMIT_3000:
        amount_w = calculate_parts(width) * 2
    else:
        amount_w = [as_number(width), as_number(width)]

    return count_frequencies(amount_w), count_frequencies(amount_h)


def get_price_k1(amount_w: dict, amount_h: dict) -> Decimal:
    amount = sum(amount_w.values()) + sum(amount_h.values())
    return (to_decimal(amount) * get_price("1К") * get_length("1К")) / THOUSAND


def amount_2(scheme_name: str) -> int:
    return get_door_amount(scheme_name)


def get_price_2(scheme_name: str) -> Decimal:
    return (
        get_price("2") * to_decimal(amount_2(scheme_name)) * get_length("1К") / THOUSAND
    )


def get_price_3k(portal_height) -> Decimal:
    return (TWO * get_price("3К") * get_length("3К")) / THOUSAND


def get_price_4k(has_rain: bool, portal_width, scheme_name: str, do_round=True) -> dict:
    zero_result = {
        "w_list": ZERO,
        "price": ZERO,
    }

    if not has_rain:
        return zero_result

    fixed_sash = get_fixed_sash_amount(scheme_name)
    doors = get_door_amount(scheme_name)
    stvorki = doors + fixed_sash

    if stvorki == 0:
        return zero_result

    result = to_decimal(portal_width) / to_decimal(stvorki)

    if result < LIMIT_3000 and do_round:
        result = dec_ceil(result / HUNDRED) * HUNDRED

    price = result * to_decimal(fixed_sash) * get_price("4К") / THOUSAND

    return {
        "w_list": as_number(result),
        "price": price,
    }


def get_price_5k(has_rain: bool, portal_width, portal_height, scheme_name: str) -> dict:
    fixed_sash = get_fixed_sash_amount(scheme_name)
    doors = get_door_amount(scheme_name)
    stvorki = doors + fixed_sash

    if stvorki == 0:
        return {
            "price": ZERO,
            "w_list": {},
            "h_list": {},
        }

    price = get_price("5К")
    length = get_length("5К")

    height = as_number(portal_height)
    amount_h = [height, height] * fixed_sash

    half_w = int(dec_ceil(to_decimal(portal_width) / to_decimal(stvorki)))

    price_h = to_decimal(len(amount_h)) * price * length / THOUSAND

    if not has_rain:
        amount_w = [half_w, half_w] * fixed_sash + [half_w + 55] * doors
    else:
        amount_w = [half_w] * fixed_sash + [half_w + 55] * doors

    upgrade_w = process_list(amount_w)

    price_w = to_decimal(len(upgrade_w)) * price * length / THOUSAND

    result = {
        "price": price_w + price_h,
        "w_list": count_frequencies(amount_w),
        "h_list": count_frequencies(amount_h),
    }

    if has_rain:
        result["price"] += get_price_4k(
            True,
            portal_width,
            scheme_name,
            do_round=False,
        )["price"]

    return result


def get_price_6k(has_rain: bool, portal_width, scheme_name: str) -> dict:
    if not has_rain:
        return {
            "price": ZERO,
            "w_list": {0: 0},
        }

    doors = get_door_amount(scheme_name)
    stvorki = doors + get_fixed_sash_amount(scheme_name)

    if stvorki == 0:
        return {
            "price": ZERO,
            "w_list": {0: 0},
        }

    result = dec_ceil(to_decimal(portal_width) / to_decimal(stvorki)) + ONE_HUNDRED_TEN

    if result < LIMIT_3000:
        result = dec_ceil(result / HUNDRED) * HUNDRED

    price = result * to_decimal(doors) * get_price("6К") / THOUSAND

    return {
        "price": price,
        "w_list": {as_number(result): doors},
    }


def get_price_7k(has_rain: bool, portal_width, portal_height, scheme_name: str) -> dict:
    doors = get_door_amount(scheme_name)
    stvorki = doors + get_fixed_sash_amount(scheme_name)

    if stvorki == 0:
        return {
            "price": ZERO,
            "h_list": {},
        }

    w = int(dec_ceil(to_decimal(portal_width) / to_decimal(stvorki)) + ONE_HUNDRED_TEN)

    height = as_number(portal_height)
    amount_h = [height, height] * doors
    amount_w = [w] * doors if not has_rain else []

    price = (
        to_decimal(len(amount_h) + len(amount_w))
        * get_price("7К")
        * get_length("7К")
        / THOUSAND
    )

    result = {
        "price": price,
        "h_list": count_frequencies(amount_h),
    }

    if amount_w:
        result["w_list"] = count_frequencies(amount_w)

    return result


def get_price_8k(portal_width, scheme_name: str, beam_id="8К") -> dict:
    doors = get_door_amount(scheme_name)
    stvorki = doors + get_fixed_sash_amount(scheme_name)

    if stvorki == 0:
        return {
            "price": ZERO,
            "w_list": {0: 0},
        }

    w = dec_ceil(to_decimal(portal_width) / to_decimal(stvorki)) + ONE_HUNDRED_TEN

    if w < LIMIT_3000:
        w = dec_ceil(w / HUNDRED) * HUNDRED

    w_num = as_number(w)
    amount_w = [w_num] * doors

    price = w * to_decimal(doors) * get_price(beam_id) / THOUSAND

    return {
        "price": price,
        "w_list": count_frequencies(amount_w),
    }


def get_price_9c(portal_width, portal_height, scheme_name: str) -> dict:
    doors = get_door_amount(scheme_name)
    stvorki = doors + get_fixed_sash_amount(scheme_name)

    if stvorki == 0:
        return {
            "price": ZERO,
            "w_list": {},
            "h_list": {},
        }

    w = int(dec_ceil(to_decimal(portal_width) / to_decimal(stvorki)))
    height = as_number(portal_height)

    amount_h = [height, height] * doors
    amount_w = [w, w] * doors

    price = (
        to_decimal(len(amount_h) + len(amount_w))
        * get_price("9С")
        * get_length("9С")
        / THOUSAND
    )

    return {
        "price": price,
        "w_list": count_frequencies(amount_w),
        "h_list": count_frequencies(amount_h),
    }


def get_price_11k(portal_width) -> dict:
    width = to_decimal(portal_width)

    price = width * get_price("11К") / THOUSAND

    return {
        "price": price,
        "w_list": {as_number(width): 1},
    }


def get_price_12c(portal_width, portal_height, scheme_name: str) -> dict:
    doors = get_door_amount(scheme_name)
    stvorki = doors + get_fixed_sash_amount(scheme_name)

    if stvorki == 0:
        return {
            "price": ZERO,
            "w_list": {},
            "h_list": {},
        }

    height = as_number(portal_height)
    amount_h = [height, height] * doors

    w = int(dec_ceil(to_decimal(portal_width) / to_decimal(stvorki)) + ONE_HUNDRED_TEN)
    amount_w = [w] * doors

    price = (
        to_decimal(len(amount_h) + len(amount_w))
        * get_price("12С")
        * get_length("12С")
        / THOUSAND
    )

    return {
        "price": price,
        "w_list": count_frequencies(amount_w),
        "h_list": count_frequencies(amount_h),
    }


def get_price_13c(portal_width, scheme_name: str) -> dict:
    doors = get_door_amount(scheme_name)
    stvorki = doors + get_fixed_sash_amount(scheme_name)

    if stvorki == 0:
        return {
            "price": ZERO,
            "w_list": {},
        }

    w = int(dec_ceil(to_decimal(portal_width) / to_decimal(stvorki)) + ONE_HUNDRED_TEN)
    amount_w = [w] * doors

    price = to_decimal(len(amount_w)) * get_price("13С") * get_length("13С") / THOUSAND

    return {
        "price": price,
        "w_list": count_frequencies(amount_w),
    }


def get_price_14c(portal_height, scheme_name: str) -> dict:
    doors = get_door_amount(scheme_name)
    height = as_number(portal_height)
    amount_h = [height, height] * doors

    price = to_decimal(len(amount_h)) * get_price("14С") * get_length("14С") / THOUSAND

    return {
        "price": price,
        "h_list": count_frequencies(amount_h),
    }


def get_rails_price(portal_width, scheme_name: str, rail_id: str) -> dict:
    rails_amount = get_rails_amount(scheme_name)
    width = to_decimal(portal_width)

    amount_w = [as_number(width)] * rails_amount

    price = width * to_decimal(rails_amount) * get_price(rail_id) / THOUSAND

    return {
        "price": price,
        "w_list": count_frequencies(amount_w),
    }


def calculate_hardware(scheme_name: str, hardware_type: str) -> dict:
    doors = get_door_amount(scheme_name)
    hw = Hardware.objects.get(name=hardware_type)

    price = to_decimal(hw.price) * to_decimal(doors)
    length = as_number(hw.length) if hw.length is not None else ZERO

    return {
        "price": price,
        "w_list": {length: doors},
    }


def calculate_color(color: str, scheme_name: str, portal_width, portal_height) -> dict:
    door_count = get_door_amount(scheme_name)
    fixed_sash_count = get_fixed_sash_amount(scheme_name)
    door_area = get_door_area(portal_width, portal_height, scheme_name)

    first_rate_door, second_rate_door = get_coverage_rate_doors(color)
    first_rate_sash, second_rate_sash = get_coverage_rate_sashes(color)
    first_price_color, second_price_color = get_price_color(color)

    first_color_amount = dec_round(
        door_area
        * (
            to_decimal(door_count) * first_rate_door
            + to_decimal(fixed_sash_count) * first_rate_sash
        ),
        2,
    )

    second_color_amount = dec_round(
        door_area
        * (
            to_decimal(door_count) * second_rate_door
            + to_decimal(fixed_sash_count) * second_rate_sash
        ),
        2,
    )

    name_dict = {
        "RAL": ["RAL-эмаль", "RAL-грунт"],
        "Лесс": ["Лесс-лак", "Лесс-грунт"],
    }

    return {
        name_dict[color][0]: {
            "price": money(first_price_color * first_color_amount),
            "w_list": {"-": first_color_amount},
        },
        name_dict[color][1]: {
            "price": money(second_price_color * second_color_amount),
            "w_list": {"-": second_color_amount},
        },
    }


def calculate_glass(
    scheme_name: str, glass_type: str, portal_width, portal_height,
) -> dict:
    glass_door_w_sub = get_sub_num("door", scheme_name)
    glass_sash_w_sub = get_sub_num("sash", scheme_name)

    doors_amount = get_door_amount(scheme_name)
    sashes_amount = get_fixed_sash_amount(scheme_name)
    stvorki = doors_amount + sashes_amount

    if stvorki == 0:
        return {
            "doors": {
                "price": ZERO,
                "w_list": {0: "-"},
                "h_list": {0: 0},
            },
            "sashes": {
                "price": ZERO,
                "w_list": {0: "-"},
                "h_list": {0: 0},
            },
        }

    width_dec = to_decimal(portal_width)
    height_dec = to_decimal(portal_height)
    stvorki_dec = to_decimal(stvorki)

    glass_door_w = int(dec_round((width_dec / stvorki_dec) - glass_door_w_sub, 0))
    glass_door_h = as_number(height_dec - GLASS_HEIGHT_DOOR_SUB)

    sash_door_w = int(dec_round((width_dec / stvorki_dec) - glass_sash_w_sub, 0))
    sash_door_h = as_number(height_dec - GLASS_HEIGHT_SASH_SUB)

    glass_price = get_glass_price(glass_type)

    doors_price = money(
        to_decimal(glass_door_w)
        * to_decimal(glass_door_h)
        * to_decimal(doors_amount)
        * glass_price
        / MILLION,
    )

    sashes_price = money(
        to_decimal(sash_door_w)
        * to_decimal(sash_door_h)
        * to_decimal(sashes_amount)
        * glass_price
        / MILLION,
    )

    return {
        "doors": {
            "price": doors_price,
            "w_list": {glass_door_w: "-"},
            "h_list": {glass_door_h: doors_amount},
        },
        "sashes": {
            "price": sashes_price,
            "w_list": {sash_door_w: "-"},
            "h_list": {sash_door_h: sashes_amount},
        },
    }


def calculate_work(workpiece: dict, portal_width, portal_height) -> dict:
    result = {
        scheme: {beam: {"столяр": ZERO, "маляр": ZERO} for beam in BEAM_LIST_FOR_WORK}
        for scheme in workpiece
    }

    for scheme in workpiece.keys():
        for beam in BEAM_LIST_FOR_WORK:
            data = workpiece[scheme].get(beam, {})

            if not isinstance(data, dict) or not data.get("price"):
                continue

            try:
                beam_price_carpenter = get_salary(beam, "carpenter")
                beam_price_painter = get_salary(beam, "painter")
            except Exception:
                continue

            has_w_list = data.get("w_list", False)
            has_h_list = data.get("h_list", False)

            if _contains_dash(has_w_list) or _contains_dash(has_h_list):
                continue

            if has_w_list and has_h_list:
                common_length = mul_dict(has_w_list) + mul_dict(has_h_list)

                result[scheme][beam] = {
                    "столяр": dec_ceil(common_length * beam_price_carpenter / THOUSAND),
                    "маляр": dec_ceil(common_length * beam_price_painter / THOUSAND),
                }
                continue

            if has_w_list:
                mul_w = mul_dict(has_w_list)

                result[scheme][beam] = {
                    "столяр": dec_ceil(mul_w * beam_price_carpenter / THOUSAND),
                    "маляр": dec_ceil(mul_w * beam_price_painter / THOUSAND),
                }
                continue

            if has_h_list:
                mul_h = mul_dict(has_h_list)

                result[scheme][beam] = {
                    "столяр": dec_ceil(mul_h * beam_price_carpenter / THOUSAND),
                    "маляр": dec_ceil(mul_h * beam_price_painter / THOUSAND),
                }

        door_amount = get_door_amount(scheme)
        sash_amount = get_fixed_sash_amount(scheme)
        stvorki = door_amount + sash_amount
        area = get_door_area(portal_width, portal_height, scheme)

        result[scheme]["Створка"] = {
            "столяр": dec_ceil(area * get_salary("door", "carpenter")),
            "маляр": dec_ceil(area * get_salary("door", "painter")),
        }

        result[scheme]["Замок"] = {
            "столяр": dec_ceil(to_decimal(door_amount) * get_salary("lock", "carpenter")),
            "маляр": dec_ceil(to_decimal(door_amount) * get_salary("lock", "painter")),
        }

        result[scheme]["Упаковка"] = {
            "столяр": dec_ceil(to_decimal(stvorki) * get_salary("package", "carpenter")),
            "маляр": dec_ceil(to_decimal(stvorki) * get_salary("package", "painter")),
        }

    return result


def summ_work(data: dict) -> dict:
    result = {
        "столяр": ZERO,
        "маляр": ZERO,
    }

    for beam_data in data.values():
        if not isinstance(beam_data, dict):
            continue

        result["столяр"] += to_decimal(beam_data.get("столяр", ZERO))
        result["маляр"] += to_decimal(beam_data.get("маляр", ZERO))

    return {
        "столяр": dec_ceil(result["столяр"]),
        "маляр": dec_ceil(result["маляр"]),
    }


def calculate_beams(
    name: str,
    width: int,
    height: int,
    has_rain: bool,
    hardware: str,
    color: str,
    glazing: str,
    scheme: str,
    wood_type: str,
    amount: int,
    **kwargs,
):
    try:
        wood_obj = PortalWood.objects.get(name=str(wood_type).lower())
        wood_ratio = to_decimal(wood_obj.ratio, default="1")
    except Exception:
        wood_ratio = Decimal("1")

    target_beams = [
        "1К",
        "2",
        "3К",
        "4К",
        "5К",
        "6К",
        "7К",
        "8К",
        "9С",
        "10К",
        "11К",
        "14С",
    ]

    workpiece = {scheme: {}}
    work_data = {scheme: []}

    amount_w, amount_h = amount_k1(width, height)
    height_num = as_number(height)

    workpiece[scheme]["1К"] = {
        "price": get_price_k1(amount_w, amount_h),
        "w_list": amount_w,
        "h_list": amount_h,
    }

    workpiece[scheme]["2"] = {
        "price": get_price_2(scheme),
        "h_list": {height_num: amount_2(scheme)},
    }

    workpiece[scheme]["3К"] = {
        "price": get_price_3k(height),
        "h_list": {height_num: 2},
    }

    if has_rain:
        dict_4k = get_price_4k(has_rain, width, scheme)
        workpiece[scheme]["4К"] = {
            "price": dict_4k["price"],
            "w_list": {dict_4k["w_list"]: get_fixed_sash_amount(scheme)},
        }
    else:
        workpiece[scheme]["4К"] = {
            "price": ZERO,
            "w_list": {0: 0},
        }

    workpiece[scheme]["5К"] = get_price_5k(
        has_rain,
        width,
        height,
        scheme,
    )

    workpiece[scheme]["6К"] = get_price_6k(
        has_rain,
        width,
        scheme,
    )

    workpiece[scheme]["7К"] = get_price_7k(
        has_rain,
        width,
        height,
        scheme,
    )

    workpiece[scheme]["8К"] = get_price_8k(width, scheme)

    workpiece[scheme]["9С"] = get_price_9c(width, height, scheme)

    workpiece[scheme]["10К"] = get_price_8k(
        width,
        scheme,
        beam_id="10К",
    )

    workpiece[scheme]["11К"] = get_price_11k(width)

    workpiece[scheme]["12С"] = get_price_12c(width, height, scheme)

    workpiece[scheme]["13С"] = get_price_13c(width, scheme)

    workpiece[scheme]["14С"] = get_price_14c(height, scheme)

    workpiece[scheme]["ЮП-968"] = get_rails_price(width, scheme, "ЮП-968")
    workpiece[scheme]["ЮП-969"] = get_rails_price(width, scheme, "ЮП-969")

    workpiece[scheme]["Фурнитура"] = calculate_hardware(scheme, hardware)

    name_dict = {
        "RAL": ["RAL-эмаль", "RAL-грунт"],
        "Лесс": ["Лесс-лак", "Лесс-грунт"],
    }

    color_data = calculate_color(color, scheme, width, height)

    for color_item_name in name_dict.get(color, []):
        workpiece[scheme][color_item_name] = color_data[color_item_name]

    glass_data = calculate_glass(scheme, glazing, width, height)

    workpiece[scheme]["Стеклопакет створка"] = glass_data["doors"]
    workpiece[scheme]["Стеклопакет глухарь"] = glass_data["sashes"]

    for beam_name in target_beams:
        item = workpiece[scheme].get(beam_name)

        if isinstance(item, dict) and "price" in item:
            item["price"] = money(to_decimal(item["price"]) * wood_ratio)
        elif isinstance(item, (int, float, Decimal)):
            workpiece[scheme][beam_name] = money(to_decimal(item) * wood_ratio)

    calculated_work = calculate_work(workpiece, width, height)[scheme]
    work_data[scheme] = calculated_work

    work_result = summ_work(calculated_work)

    workpiece[scheme]["Работа столяр"] = {
        "price": work_result["столяр"],
        "w_list": {"-": "-"},
    }

    workpiece[scheme]["Работа маляр"] = {
        "price": work_result["маляр"],
        "w_list": {"-": "-"},
    }

    portal_total_raw = ZERO

    for value in workpiece[scheme].values():
        if isinstance(value, dict) and "price" in value:
            portal_total_raw += to_decimal(value["price"])

    portal_total = money(portal_total_raw * to_decimal(amount))

    scheme_ratio = to_decimal(
        Scheme.objects.get(name=scheme).ratio,
        default="1",
    )

    portal_total_with_ratio = money(portal_total * scheme_ratio)

    return (
        workpiece,
        work_data,
        portal_total,
        scheme_ratio,
        portal_total_with_ratio,
    )


def calculate_portals(portals: list) -> dict:
    result = {}
    total_price = ZERO
    total_price_with_ratio = ZERO

    for portal in portals:
        (
            workpiece,
            work_data,
            portal_total,
            scheme_ratio,
            portal_total_with_ratio,
        ) = calculate_beams(**portal)

        result[portal["name"]] = {
            "workpiece": workpiece,
            "work_data": work_data,
            "portal_total": portal_total,
            "scheme_ratio": scheme_ratio,
            "portal_total_with_ratio": portal_total_with_ratio,
            "type": "portal",
            "N": portal.get("amount"),
        }

        total_price += to_decimal(portal_total)
        total_price_with_ratio += to_decimal(portal_total_with_ratio)

    result["ИТОГО"] = money(total_price)
    result["ИТОГО_С_КОЭФФИЦИЕНТОМ"] = money(total_price_with_ratio)

    return result


def calculate_glukhar_color(color: str, width, height, n_amount) -> dict:
    crd_varnish, crd_grunt = get_coverage_rate_doors(color)
    price_varnish, price_grunt = get_price_color(color)

    area = to_decimal(width) * to_decimal(height) / MILLION
    n_amount_dec = to_decimal(n_amount)

    grunt_amount = dec_round(crd_grunt * area, 2)
    varnish_amount = dec_round(crd_varnish * area, 2)

    varnish_price = dec_ceil(varnish_amount * price_varnish)
    grunt_price = dec_ceil(grunt_amount * price_grunt)

    first_color_name = "RAL-эмаль" if color == "RAL" else "Лесс-лак"

    return {
        first_color_name: {
            "price": varnish_price,
            "length": "-",
            "amount": varnish_amount,
            "N_amount": dec_round(varnish_amount * n_amount_dec, 2),
            "N_price": money(varnish_price * n_amount_dec),
        },
        f"{color}-грунт": {
            "price": grunt_price,
            "length": "-",
            "amount": grunt_amount,
            "N_amount": dec_round(grunt_amount * n_amount_dec, 2),
            "N_price": money(grunt_price * n_amount_dec),
        },
    }


def calculate_glukhar_glass(width, height, amount, is_not_rectangle=False) -> dict:
    unloading = ZERO

    width_dec = to_decimal(width)
    height_dec = to_decimal(height)

    glukhar_width = width_dec - TWO * GLUKHAR_GLASS_SUB
    glukhar_height = height_dec - TWO * GLUKHAR_GLASS_SUB

    glass_area = glukhar_width * glukhar_height / MILLION

    price_area = TEN if is_not_rectangle else glass_area

    price_glass = money(get_price_glass_glukhar_on_area(price_area) * glass_area)

    if glass_area * WEIGHT_GLASS_CONST >= ONE_HUNDRED_SIXTY:
        unloading = FOURTEEN_THOUSAND

    amount_dec = to_decimal(amount)

    return {
        "unloading": unloading,
        "price": price_glass,
        "length": {
            "w": as_number(glukhar_width),
            "h": as_number(glukhar_height),
        },
        "amount": 1,
        "N_amount": amount_dec,
        "N_price": money(price_glass * amount_dec),
    }


def get_all_price(result: dict) -> Decimal:
    price = ZERO

    for key, value in result.items():
        if key in ("N", "type", "ИТОГО"):
            continue

        if isinstance(value, dict) and "price" in value:
            price += to_decimal(value["price"])
        elif isinstance(value, (int, float, Decimal)):
            price += to_decimal(value)

    return price


def calculate_glukhar(glukhar_data: list) -> dict:
    result = {}
    total_price = ZERO

    for glukhar in glukhar_data:
        name = glukhar["name"]
        result[name] = {}

        width = glukhar["width"]
        height = glukhar["height"]
        amount = glukhar["amount"]
        material = glukhar["material"]
        color = glukhar["color"]
        not_rectangle = glukhar["is_not_rectangle"]

        amount_dec = to_decimal(amount)

        perimeter = find_multiple_perimeter(get_perimeter(width, height))
        bars = count_bars(width, height)

        glukhar_price = dec_ceil(get_price_glukhar(material) * perimeter)

        result[name]["N"] = amount

        result[name][f"Брус ({material})"] = {
            "price": glukhar_price,
            "length": 6000,
            "amount": bars,
            "N_amount": amount_dec * to_decimal(bars),
            "N_price": money(glukhar_price * amount_dec),
        }

        result[name].update(calculate_glukhar_color(color, width, height, amount))

        glass_info = calculate_glukhar_glass(
            width,
            height,
            amount,
            not_rectangle,
        )

        result[name]["Выгрузка"] = glass_info.pop("unloading")
        result[name]["Стеклопакет"] = glass_info

        area = to_decimal(width) * to_decimal(height) / MILLION

        carpenter_salary = dec_ceil(area * get_salary("door", "carpenter"))
        painter_salary = dec_ceil(area * get_salary("door", "painter"))

        result[name]["Работа столяра"] = {
            "price": carpenter_salary,
            "length": "-",
            "amount": 1,
            "N_amount": amount_dec,
            "N_price": money(carpenter_salary * amount_dec),
        }

        result[name]["Работа маляра"] = {
            "price": painter_salary,
            "length": "-",
            "amount": 1,
            "N_amount": amount_dec,
            "N_price": money(painter_salary * amount_dec),
        }

        item_total = get_all_price(result[name])

        result[name]["ИТОГО"] = {
            "price": item_total,
            "length": "-",
            "amount": 1,
            "N_amount": amount_dec,
            "N_price": money(item_total * amount_dec),
        }

        result[name]["type"] = "glukhar"

        total_price += result[name]["ИТОГО"]["N_price"]

    result["ИТОГО"] = money(total_price)

    return result
