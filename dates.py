import datetime
import csv


def write_day_data(day_index):
    result = {'DateKey': day_index + 1}
    cur_date = datetime.date(2017, 1, 1) + datetime.timedelta(days=day_index)
    result['Date'] = cur_date.strftime('%Y%m%d')
    result['DayNumberInMonth'] = cur_date.day
    result['DayNumberInYear'] = day_index + 1
    result['WeekNumberInYear'] = day_index // 7 + 1
    result['MonthNum'] = cur_date.month
    result['MonthTxt'] = cur_date.strftime('%B')
    result['Quarter'] = (cur_date.month - 1) // 3 + 1
    result['Year'] = 2017
    result['FiscalYear'] = 2016
    if day_index > 211:
        result['FiscalYear'] = 2017
    # New Year's, MLK, President's Day, Memorial Day, Independence Day
    # Labor Day, Columbus Day, Veteran's Day, Thanksgiving, Christmas
    result['isHoliday'] = day_index in [0, 15, 50, 148, 184, 244, 265, 298, 310, 358]
    result['isWeekend'] = day_index % 7 == 0 or day_index % 7 == 6
    if 0 <= day_index < 77:
        result['Season'] = 'Winter'
    elif day_index < 171:
        result['Season'] = 'Spring'
    elif day_index < 264:
        result['Season'] = 'Summer'
    elif day_index < 354:
        result['Season'] = 'Fall'
    else:
        result['Season'] = 'Winter'
    return result


def write_year_data():
    for i in range(365):
        yield write_day_data(i)


if __name__ == '__main__':
    field_names = ['DateKey', 'Date', 'DayNumberInMonth', 'DayNumberInYear', 'WeekNumberInYear',
                   'MonthNum', 'MonthTxt', 'Quarter', 'Year', 'FiscalYear', 'isHoliday', 'isWeekend',
                   'Season']
    with open('dates.csv', 'w', newline='') as file_handle:
        writer = csv.DictWriter(file_handle, field_names)
        writer.writeheader()
        for row in write_year_data():
            writer.writerow(row)