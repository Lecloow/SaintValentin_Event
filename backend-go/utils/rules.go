package utils

import (
	"time"
)

// If you change the number of hints per day,
// be sure to update CalculatePoints and HintRevealTime
const NumberOfHintsPerDay = 3

const EventDuration = 2 // The numbers of day

var eventStartDate, _ = time.Parse("2006-01-02", "2026-05-28") // 2006-01-02 is just the format (YYYY-MM_DD)
// Be sure that you put the time in the correct format, otherwise it will crash (I guess ...)

// For every reveal time, do not care about the year, month and day
// The important part is the hour, minutes , and seconds
// The format is time.Date(year, month, day, hour, minute, second, nanosecond, location)
// Be sure to keep it in UTC, because the server will probably be in UTC, just check it before (It's not cool to discover it the day of the event, I swear)
var MatchRevealTime = time.Date(2000, 1, 1, 14, 0, 0, 0, time.UTC)

// If true a girl will be match with a boy
// else it will be with th best candidate and ignore the isMatchByGender
// You need to know that the gender is estimated by a ML using only the first name, it may be wrong
const IsMatchByGender = true
const genderMatchBonus = 0.15

func HintRevealTime(hintIndex int) time.Time {
	switch hintIndex {
	case 1:
		return time.Date(2000, 1, 1, 9, 0, 0, 0, time.UTC) // Hint 1
	case 2:
		return time.Date(2000, 1, 1, 11, 0, 0, 0, time.UTC) // Hint 2
	case 3:
		return time.Date(2000, 1, 1, 12, 0, 0, 0, time.UTC) // Hint 3
	default:
		return time.Time{} // error btw
	}
}

func CalculatePoints(hintNumber int) int {
	switch hintNumber {
	case 1:
		return 100
	case 2:
		return 75
	case 3:
		return 50
	default:
		return 0
	}
}

func getHintType(hintNumber int) []string {
	switch hintNumber {
	case 1:
		return []string{"letterInFirstName", "letterInLastName", "numberOfVowel"}[:]
	case 2:
		return []string{"firstLetterOfFirstName", "firstLetterOfLastName"}[:]
	case 3:
		return []string{"class", "firstName"}[:]
	default:
		return nil
	}
}
