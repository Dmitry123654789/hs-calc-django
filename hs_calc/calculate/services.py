from collections import Counter
from math import ceil

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


GLASS_HEIGHT_DOOR_SUB = 202
GLASS_HEIGHT_SASH_SUB = 46
GLUKHAR_GLASS_SUB = 78
WEIGHT_GLASS_CONST = 55
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


def get_price(beam_name):
    return Beams.objects.get(name=beam_name).price


def get_length(beam_name):
    return Beams.objects.get(name=beam_name).length * 1000


def get_door_amount(scheme_name):
    return Scheme.objects.get(name=scheme_name).door


def get_fixed_sash_amount(scheme_name):
    return Scheme.objects.get(name=scheme_name).fixed_sash


def get_rails_amount(scheme_name):
    return Scheme.objects.get(name=scheme_name).rail_amour


def get_coverage_rate_doors(color_prefix):
    return list(
        Color.objects.filter(name__startswith=color_prefix)
        .order_by("id")
        .values_list("coverage_rate_doors", flat=True)[:2],
    )


def get_price_color(color_prefix):
    return list(
        Color.objects.filter(name__startswith=color_prefix)
        .order_by("id")
        .values_list("price", flat=True)[:2],
    )


def get_coverage_rate_sashes(color_prefix):
    return list(
        Color.objects.filter(name__startswith=color_prefix)
        .order_by("id")
        .values_list("coverage_rate_sash", flat=True)[:2],
    )


def get_sub_num(door_type, scheme_name):
    scheme = Scheme.objects.get(name=scheme_name)
    return scheme.door_sub if door_type == "door" else scheme.sash_sub


def get_glass_price(glass_type):
    return Glass.objects.get(name=glass_type).price


def get_salary(beam_name, worker):
    work = Work.objects.get(beam=beam_name)
    return float(work.carpenter) if worker == "carpenter" else float(work.painter)


def get_price_glukhar(wood_type):
    return GlukharWood.objects.get(name=wood_type).price


def get_price_glass_glukhar_on_area(area):
    if area >= 10:
        area = 9

    return (
        GlukharGlass.objects.filter(min_area__lte=area, max_area__gt=area).first().price
    )


def mul_dict(dictionary):
    return sum(k * v for k, v in dictionary.items())


def get_door_area(portal_width, portal_height, scheme_name):
    door_count = get_door_amount(scheme_name)
    fixed_sash_count = get_fixed_sash_amount(scheme_name)
    w = ceil(portal_width / (door_count + fixed_sash_count))
    return (w * portal_height) / 1_000_000


def get_perimeter(width, height):
    return 2 * (width + height) / 1_000


def find_multiple_perimeter(perimeter, n=6):
    return ceil(perimeter / n) * n


def count_frequencies(lst):
    return dict(Counter(lst))


def process_list(lst):
    sorted_list = sorted(lst, reverse=True)
    result = []
    used = [False] * len(sorted_list)
    for i in range(len(sorted_list)):
        if used[i]:
            continue

        current = sorted_list[i]
        if current == 3000:
            result.append(3000)
            used[i] = True
            continue

        combination = [current]
        total = current
        used[i] = True
        for j in range(i + 1, len(sorted_list)):
            if not used[j] and total + sorted_list[j] <= 3000:
                total += sorted_list[j]
                combination.append(sorted_list[j])
                used[j] = True

        if len(combination) > 1:
            result.append(3000)
        else:
            result.append(current)

    return sorted(result)


def calculate_parts(total_length, part_length=3000):
    parts = []
    while total_length >= part_length:
        parts.append(part_length)
        total_length -= part_length

    if total_length > 0:
        parts.append(total_length)

    return parts


def count_bars(width: float, height: float, bar_length: float = 6) -> int:
    perimeter = find_multiple_perimeter(2 * (width + height) / 1000)
    return ceil(perimeter / bar_length)


def amount_k1(portal_width, portal_height):
    amount_h = [portal_height, portal_height]
    amount_w = [portal_width, portal_width]
    if portal_width >= 3000:
        amount_w = calculate_parts(portal_width) * 2

    return count_frequencies(amount_w), count_frequencies(amount_h)


def get_price_k1(amount_w: dict, amount_h: dict):
    amount = sum(amount_w.values()) + sum(amount_h.values())
    return (amount * get_price("1К") * get_length("1К")) / 1000


def amount_2(scheme_name):
    return get_door_amount(scheme_name)


def get_price_2(scheme_name):
    return (get_price("2") * amount_2(scheme_name) * get_length("1К")) / 1000


def get_price_3k(portal_height):
    return (2 * get_price("3К") * get_length("3К")) / 1000


def get_price_4k(has_rain, portal_width, scheme_name, do_round=True):
    if not has_rain:
        return 0

    fixed_sash = get_fixed_sash_amount(scheme_name)
    stvorki = get_door_amount(scheme_name) + fixed_sash
    result = portal_width / stvorki
    if int(result) < 3000 and do_round:
        result = ceil(result / 100) * 100

    return {"w_list": result, "price": (result * fixed_sash * get_price("4К")) / 1000}


def get_price_5k(has_rain, portal_width, portal_height, scheme_name):
    fixed_sash = get_fixed_sash_amount(scheme_name)
    doors = get_door_amount(scheme_name)
    stvorki = doors + fixed_sash
    price = get_price("5К")
    length = get_length("5К")
    amount_h = [portal_height, portal_height] * fixed_sash
    half_w = ceil(portal_width / stvorki)
    price_h = (len(amount_h) * price * length) / 1000
    amount_w = (
        [half_w, half_w] * fixed_sash + [half_w + 55] * doors
        if not has_rain
        else [half_w] * fixed_sash + [half_w + 55] * doors
    )
    upgrade_w = process_list(amount_w)
    price_w = (len(upgrade_w) * price * length) / 1000
    result = {
        "price": price_w + price_h,
        "w_list": count_frequencies(amount_w),
        "h_list": count_frequencies(amount_h),
    }
    if has_rain:
        result["price"] += get_price_4k(
            has_rain,
            portal_width,
            scheme_name,
            do_round=False,
        )["price"]

    return result


def get_price_6k(has_rain, portal_width, scheme_name):
    if not has_rain:
        return {"price": 0, "w_list": {0: 0}}

    doors = get_door_amount(scheme_name)
    stvorki = doors + get_fixed_sash_amount(scheme_name)
    result = ceil(portal_width / stvorki) + 110
    if int(result) < 3000:
        result = ceil(result / 100) * 100

    return {"price": (result * doors * get_price("6К")) / 1000, "w_list": {result: doors}}


def get_price_7k(has_rain, portal_width, portal_height, scheme_name):
    doors = get_door_amount(scheme_name)
    stvorki = doors + get_fixed_sash_amount(scheme_name)
    w = ceil(portal_width / stvorki) + 110
    amount_h = [portal_height, portal_height] * doors
    amount_w = [w] * doors if not has_rain else []
    price = (len(amount_h) + len(amount_w)) * get_price("7К") * get_length("7К") / 1000
    res = {"price": price, "h_list": count_frequencies(amount_h)}
    if amount_w:
        res["w_list"] = count_frequencies(amount_w)

    return res


def get_price_8k(portal_width, scheme_name, beam_id="8К"):
    doors = get_door_amount(scheme_name)
    stvorki = doors + get_fixed_sash_amount(scheme_name)
    w = ceil(portal_width / stvorki) + 110
    if int(w) < 3000:
        w = ceil(w / 100) * 100

    amount_w = [w] * doors
    return {
        "price": w * doors * get_price(beam_id) / 1000,
        "w_list": count_frequencies(amount_w),
    }


def get_price_9c(portal_width, portal_height, scheme_name):
    doors = get_door_amount(scheme_name)
    stvorki = doors + get_fixed_sash_amount(scheme_name)
    w = ceil(portal_width / stvorki)
    amount_h = [portal_height, portal_height] * doors
    amount_w = [w, w] * doors
    price = (len(amount_h) + len(amount_w)) * get_price("9С") * get_length("9С") / 1000
    return {
        "price": price,
        "w_list": count_frequencies(amount_w),
        "h_list": count_frequencies(amount_h),
    }


def get_price_11k(portal_width):
    return {"price": portal_width * get_price("11К") / 1000, "w_list": {portal_width: 1}}


def get_price_12c(portal_width, portal_height, scheme_name):
    doors = get_door_amount(scheme_name)
    stvorki = doors + get_fixed_sash_amount(scheme_name)
    amount_h = [portal_height, portal_height] * doors
    w = ceil(portal_width / stvorki) + 110
    amount_w = [w] * doors
    price = (len(amount_h) + len(amount_w)) * get_price("12С") * get_length("12С") / 1000
    return {
        "price": price,
        "w_list": count_frequencies(amount_w),
        "h_list": count_frequencies(amount_h),
    }


def get_price_13c(portal_width, scheme_name):
    doors = get_door_amount(scheme_name)
    stvorki = doors + get_fixed_sash_amount(scheme_name)
    w = ceil(portal_width / stvorki) + 110
    amount_w = [w] * doors
    return {
        "price": len(amount_w) * get_price("13С") * get_length("13С") / 1000,
        "w_list": count_frequencies(amount_w),
    }


def get_price_14c(portal_height, scheme_name):
    doors = get_door_amount(scheme_name)
    amount_h = [portal_height, portal_height] * doors
    return {
        "price": len(amount_h) * get_price("14С") * get_length("14С") / 1000,
        "h_list": count_frequencies(amount_h),
    }


def get_rails_price(portal_width, scheme_name, rail_id):
    rails_amount = get_rails_amount(scheme_name)
    amount_w = [portal_width] * rails_amount
    return {
        "price": portal_width * rails_amount * get_price(rail_id) / 1000,
        "w_list": count_frequencies(amount_w),
    }


def calculate_hardware(scheme_name, hardware_type):
    doors = get_door_amount(scheme_name)
    hw = Hardware.objects.get(name=hardware_type)
    return {"price": hw.price * doors, "w_list": {hw.length: doors}}


def calculate_color(color, scheme_name, portal_width, portal_height):
    door_count = get_door_amount(scheme_name)
    fixed_sash_count = get_fixed_sash_amount(scheme_name)
    door_area = get_door_area(portal_width, portal_height, scheme_name)

    # Преобразуем Decimal в float для корректного умножения
    first_rate_door, second_rate_door = [float(x) for x in get_coverage_rate_doors(color)]
    first_rate_sash, second_rate_sash = [
        float(x) for x in get_coverage_rate_sashes(color)
    ]
    first_price_color, second_price_color = [float(x) for x in get_price_color(color)]

    first_color_amount = round(
        door_area * (door_count * first_rate_door + fixed_sash_count * first_rate_sash),
        2,
    )
    second_color_amount = round(
        door_area * (door_count * second_rate_door + fixed_sash_count * second_rate_sash),
        2,
    )

    name_dict = {"RAL": ["RAL-эмаль", "RAL-грунт"], "Лесс": ["Лесс-лак", "Лесс-грунт"]}
    return {
        name_dict[color][0]: {
            "price": round(first_price_color * first_color_amount, 2),
            "w_list": {"-": first_color_amount},
        },
        name_dict[color][1]: {
            "price": round(second_price_color * second_color_amount, 2),
            "w_list": {"-": second_color_amount},
        },
    }


def calculate_glass(scheme_name, glass_type, portal_width, portal_height):
    glass_door_w_sub = get_sub_num("door", scheme_name)
    glass_sash_w_sub = get_sub_num("sash", scheme_name)
    doors_amount = get_door_amount(scheme_name)
    sashes_amount = get_fixed_sash_amount(scheme_name)
    stvorki = doors_amount + sashes_amount

    glass_door_w = (portal_width / stvorki) - glass_door_w_sub
    glass_door_h = portal_height - GLASS_HEIGHT_DOOR_SUB
    sash_door_w = (portal_width / stvorki) - glass_sash_w_sub
    sash_door_h = portal_height - GLASS_HEIGHT_SASH_SUB
    glass_price = get_glass_price(glass_type)

    return {
        "doors": {
            "price": glass_door_w * glass_door_h * doors_amount * glass_price / 1_000_000,
            "w_list": {glass_door_w: "-"},
            "h_list": {glass_door_h: doors_amount},
        },
        "sashes": {
            "price": sash_door_w * sash_door_h * sashes_amount * glass_price / 1_000_000,
            "w_list": {sash_door_w: "-"},
            "h_list": {sash_door_h: sashes_amount},
        },
    }


def calculate_work(workpiece: dict, portal_width, portal_height):
    result = {scheme: dict.fromkeys(BEAM_LIST_FOR_WORK, 0) for scheme in workpiece}
    for scheme in workpiece.keys():
        for beam in BEAM_LIST_FOR_WORK:
            data = workpiece[scheme].get(beam, {})
            if not data.get("price"):
                result[scheme][beam] = {"столяр": 0, "маляр": 0}
                continue

            try:
                beam_price_carpenter = get_salary(beam, "carpenter")
                beam_price_painter = get_salary(beam, "painter")
            except Exception:
                continue

            has_w_list = data.get("w_list", False)
            has_h_list = data.get("h_list", False)

            if has_w_list and has_h_list:
                mul_w, mul_h = mul_dict(has_w_list), mul_dict(has_h_list)
                result[scheme][beam] = {
                    "столяр": ceil(
                        (mul_w * beam_price_carpenter + mul_h * beam_price_carpenter)
                        / 1000,
                    ),
                    "маляр": ceil(
                        (mul_w * beam_price_painter + mul_h * beam_price_painter) / 1000,
                    ),
                }
                continue

            if has_w_list:
                if "-" in has_w_list.keys() or "-" in has_w_list.values():
                    continue

                mul_w = mul_dict(has_w_list)
                result[scheme][beam] = {
                    "столяр": ceil(mul_w * beam_price_carpenter / 1000),
                    "маляр": ceil(mul_w * beam_price_painter / 1000),
                }

            if has_h_list:
                mul_h = mul_dict(has_h_list)
                result[scheme][beam] = {
                    "столяр": ceil(mul_h * beam_price_carpenter / 1000),
                    "маляр": ceil(mul_h * beam_price_painter / 1000),
                }

        door_amount = get_door_amount(scheme)
        sachs_amount = get_fixed_sash_amount(scheme)
        stvorki = door_amount + sachs_amount
        area = get_door_area(portal_width, portal_height, scheme)

        result[scheme]["Створка"] = {
            "столяр": ceil(area * get_salary("door", "carpenter")),
            "маляр": ceil(area * get_salary("door", "painter")),
        }
        result[scheme]["Замок"] = {
            "столяр": ceil(door_amount * get_salary("lock", "carpenter")),
            "маляр": ceil(door_amount * get_salary("lock", "painter")),
        }
        result[scheme]["Упаковка"] = {
            "столяр": ceil(stvorki * get_salary("package", "carpenter")),
            "маляр": ceil(stvorki * get_salary("package", "painter")),
        }

    return result


def summ_work(data):
    res = {"столяр": 0, "маляр": 0}
    for beam in data:
        res["столяр"] += ceil(data[beam]["столяр"])
        res["маляр"] += ceil(data[beam]["маляр"])

    return {"столяр": ceil(res["столяр"]), "маляр": ceil(res["маляр"])}


def calculate_beams(
    portal_width: int,
    portal_height: int,
    has_rain: bool,
    hardware: str,
    color: str,
    glass_type: str,
    schemes: list,
    wood_type: str,
):
    try:
        wood_obj = PortalWood.objects.get(name=wood_type.lower())
        wood_ratio = float(wood_obj.ratio)
    except (PortalWood.DoesNotExist, ValueError, TypeError):
        wood_ratio = 1.0

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

    workpiece = {scheme: {} for scheme in schemes}
    work_data = {scheme: [] for scheme in schemes}

    for scheme in schemes:
        amount_w, amount_h = amount_k1(portal_width, portal_height)
        workpiece[scheme]["1К"] = {
            "price": get_price_k1(amount_w, amount_h),
            "w_list": amount_w,
            "h_list": amount_h,
        }
        workpiece[scheme]["2"] = {
            "price": get_price_2(scheme),
            "h_list": {portal_height: amount_2(scheme)},
        }
        workpiece[scheme]["3К"] = {
            "price": get_price_3k(portal_height),
            "h_list": {portal_height: 2},
        }

        if has_rain:
            dict_4k = get_price_4k(has_rain, portal_width, scheme)
            workpiece[scheme]["4К"] = {
                "price": dict_4k["price"],
                "w_list": {dict_4k["w_list"]: get_fixed_sash_amount(scheme)},
            }
        else:
            workpiece[scheme]["4К"] = {"price": 0, "w_list": {0: 0}}

        workpiece[scheme]["5К"] = get_price_5k(
            has_rain,
            portal_width,
            portal_height,
            scheme,
        )
        workpiece[scheme]["6К"] = get_price_6k(has_rain, portal_width, scheme)
        workpiece[scheme]["7К"] = get_price_7k(
            has_rain,
            portal_width,
            portal_height,
            scheme,
        )
        workpiece[scheme]["8К"] = get_price_8k(portal_width, scheme)
        workpiece[scheme]["9С"] = get_price_9c(portal_width, portal_height, scheme)
        workpiece[scheme]["10К"] = get_price_8k(portal_width, scheme, beam_id="10К")
        workpiece[scheme]["11К"] = get_price_11k(portal_width)
        workpiece[scheme]["12С"] = get_price_12c(portal_width, portal_height, scheme)
        workpiece[scheme]["13С"] = get_price_13c(portal_width, scheme)
        workpiece[scheme]["14С"] = get_price_14c(portal_height, scheme)
        workpiece[scheme]["ЮП-968"] = get_rails_price(portal_width, scheme, "ЮП-968")
        workpiece[scheme]["ЮП-969"] = get_rails_price(portal_width, scheme, "ЮП-969")
        workpiece[scheme]["Фурнитура"] = calculate_hardware(scheme, hardware)

        name_dict = {
            "RAL": ["RAL-эмаль", "RAL-грунт"],
            "Лесс": ["Лесс-лак", "Лесс-грунт"],
        }
        data = calculate_color(color, scheme, portal_width, portal_height)
        for name in name_dict[color]:
            workpiece[scheme][name] = data[name]

        glass_data = calculate_glass(scheme, glass_type, portal_width, portal_height)
        workpiece[scheme]["Стеклопакет створка"] = glass_data["doors"]
        workpiece[scheme]["Стеклопакет глухарь"] = glass_data["sashes"]

    for scheme in schemes:
        for beam_name in target_beams:
            if beam_name in workpiece[scheme]:
                item = workpiece[scheme][beam_name]
                if isinstance(item, dict) and "price" in item:
                    item["price"] = round(item["price"] * wood_ratio, 2)
                elif isinstance(item, (int, float)):
                    workpiece[scheme][beam_name] = round(item * wood_ratio, 2)

    for scheme in schemes:
        calculated_work = calculate_work(workpiece, portal_width, portal_height)[scheme]
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

    return workpiece, work_data


def calculate_glukhar_color(color, width, height, n_amount) -> dict:
    crd_varnish, crd_grunt = [float(x) for x in get_coverage_rate_doors(color)]
    glukhar_area = width * height / 1_000_000
    price_varnish, price_grunt = [float(x) for x in get_price_color(color)]

    grunt_amount = round(crd_grunt * glukhar_area, 2)
    varnish_amount = round(crd_varnish * glukhar_area, 2)

    first_color_name = "RAL-эмаль" if color == "RAL" else "Лесс-лак"

    return {
        first_color_name: {
            "price": ceil(varnish_amount * price_varnish),
            "length": "-",
            "amount": varnish_amount,
            "N_amount": varnish_amount * n_amount,
            "N_price": ceil(varnish_amount * price_varnish) * n_amount,
        },
        f"{color}-грунт": {
            "price": ceil(grunt_amount * price_grunt),
            "length": "-",
            "amount": grunt_amount,
            "N_amount": grunt_amount * n_amount,
            "N_price": ceil(grunt_amount * price_grunt) * n_amount,
        },
    }


def calculate_glukhar_glass(width, height, amount, is_not_rectangle=False):
    unloading = 0
    glukar_width = width - 2 * GLUKHAR_GLASS_SUB
    glukar_height = height - 2 * GLUKHAR_GLASS_SUB
    glass_area = glukar_width * glukar_height / 1_000_000
    price_glass = (
        get_price_glass_glukhar_on_area(glass_area if not is_not_rectangle else 10)
        * glass_area
    )
    if glass_area * WEIGHT_GLASS_CONST >= 160:
        unloading = 14_000

    return {
        "unloading": unloading,
        "price": price_glass,
        "length": {"w": glukar_width, "h": glukar_height},
        "amount": 1,
        "N_amount": amount,
        "N_price": price_glass * amount,
    }


def get_all_price(result):
    price = 0
    for beam, _ in result.items():
        if beam == "N":
            continue

        price += result[beam] if isinstance(result[beam], int) else result[beam]["price"]

    return price


def calculate_glukhar(glukhar_data: dict):
    result = {}
    material = glukhar_data.pop("material")
    color = glukhar_data.pop("color")
    for glukhar in glukhar_data:
        result[glukhar] = {}
        width = glukhar_data[glukhar]["width"]
        height = glukhar_data[glukhar]["height"]
        amount = glukhar_data[glukhar]["amount"]
        not_rectangle = glukhar_data[glukhar]["is_not_rectangle"]

        glukhar_price = ceil(
            get_price_glukhar(material)
            * find_multiple_perimeter(get_perimeter(width, height)),
        )
        result[glukhar]["N"] = amount
        result[glukhar][f"Брус ({material})"] = {
            "price": glukhar_price,
            "length": 6000,
            "amount": count_bars(width, height),
            "N_amount": amount * count_bars(width, height),
            "N_price": amount * glukhar_price,
        }

        for keys, values in calculate_glukhar_color(color, width, height, amount).items():
            result[glukhar][keys] = values

        glass_info = calculate_glukhar_glass(width, height, amount, not_rectangle)
        result[glukhar]["Выгрузка"] = glass_info.pop("unloading")
        result[glukhar]["Стеклопакет"] = glass_info

        carpenter_salary = ceil(
            (width * height / 1_000_000) * get_salary("door", "carpenter"),
        )
        painter_salary = ceil(
            (width * height / 1_000_000) * get_salary("door", "painter"),
        )
        result[glukhar]["Работа столяра"] = {
            "price": carpenter_salary,
            "length": "-",
            "amount": 1,
            "N_amount": amount,
            "N_price": amount * carpenter_salary,
        }
        result[glukhar]["Работа маляра"] = {
            "price": painter_salary,
            "length": "-",
            "amount": 1,
            "N_amount": amount,
            "N_price": amount * painter_salary,
        }

        total_price = get_all_price(result[glukhar])
        result[glukhar]["ИТОГО"] = {
            "price": total_price,
            "length": "-",
            "amount": 1,
            "N_amount": amount,
            "N_price": amount * total_price,
        }

    return result
