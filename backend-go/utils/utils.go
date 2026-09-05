package utils

import (
	"backend/models"
	"backend/utils/ml"
	"crypto/rand"
	"encoding/base64"
	"errors"
	"math/big"
	mathrand "math/rand"
	"regexp"
	"strconv"
	"time"

	"github.com/jackc/pgx/v5/pgconn"
	"golang.org/x/crypto/bcrypt"
)

func GenerateSecureToken() string {
	b := make([]byte, 32)
	_, err := rand.Read(b)
	if err != nil {
		return ""
	}
	return base64.URLEncoding.EncodeToString(b)
}

func GetCurrentDay() int {
	// Implement logic to determine the current day of the event
	// For example, if the event starts on a specific date, calculate the difference in days from that date to today
	daysPassed := int(time.Since(eventStartDate).Hours() / 24)
	return daysPassed + 1
}

func GetRevealTime(revealTime time.Time, day int) time.Time {
	dayDate := eventStartDate.AddDate(0, 0, day-1)

	return time.Date(
		dayDate.Year(),
		dayDate.Month(),
		dayDate.Day(),
		revealTime.Hour(),
		revealTime.Minute(),
		revealTime.Second(),
		0, // nanoseconds
		time.UTC,
	)
}

func RandomHintType(hintNumber int) string {
	types := getHintType(hintNumber)
	index := mathrand.Intn(len(types))
	return types[index]
}

func GenerateHintContent(match models.User, hintType string) string {
	switch hintType {
	case "letterInFirstName":
		return countLetters(match.FirstName)
	case "letterInLastName":
		return countLetters(match.LastName)
	case "numberOfVowel":
		return countVowels(match.LastName)
	case "firstLetterOfFirstName":
		return string(match.FirstName[0])
	case "firstLetterOfLastName":
		return string(match.LastName[0])
	case "class":
		return match.Class
	case "firstName":
		return match.FirstName
	default:
		return "" // error btw
	}
}

func countVowels(text string) string {
	re := regexp.MustCompile("[aeiouAEIOUáéíóúÁÉÍÓÚàèìòùÀÈÌÒÙâêîôûÂÊÎÔÛäëïöüÄËÏÖÜ]")
	matches := re.FindAllString(text, -1)
	return strconv.Itoa(len(matches))
}

func countLetters(text string) string {
	re := regexp.MustCompile("[a-zA-Z]")
	matches := re.FindAllString(text, -1)
	return strconv.Itoa(len(matches))
}

func GenerateRevealCode() (string, error) {
	charsets := "abcdefghijklmnopqrstuvwxyz0123456789"
	var length = 6

	revealCode, err := GenerateString(charsets, length)
	if err != nil {
		return "", err
	}

	return revealCode, nil
}

func GeneratePassword(length int) (string, error) {
	charsets := "abcdefghijklmnopqrstuvwxyz0123456789"

	password, err := GenerateString(charsets, length)
	if err != nil {
		return "", err
	}

	return password, nil
}

func GenerateString(charsets string, length int) (string, error) {
	result := make([]byte, length)
	charsetLen := big.NewInt(int64(len(charsets)))

	for i := range length {
		randomIndex, err := rand.Int(rand.Reader, charsetLen)
		if err != nil {
			return "", err
		}

		result[i] = charsets[randomIndex.Int64()]
	}

	return string(result), nil
}

func MatchScore(a, b []int16) float64 {
	if len(a) != len(b) {
		return 0
	}
	matches := 0
	for i := range a {
		if a[i] == b[i] {
			matches++
		}
	}
	return float64(matches) / float64(len(a))
}

func IsUniqueViolation(err error) bool {
	var pgErr *pgconn.PgError
	if errors.As(err, &pgErr) {
		return pgErr.Code == "23505"
	}
	return false
}

func HashPassword(password string) (string, error) {
	bytes, err := bcrypt.GenerateFromPassword([]byte(password), 14)
	return string(bytes), err
}

func GetGender(name string) string {
	return ml.GetGender(name)
}

func IsGenderCompatible(genderA, genderB string) float64 {
	if (genderA == "Female" && genderB == "Male") || // Unisex is neutral.
		(genderA == "Male" && genderB == "Female") {
		return genderMatchBonus
	}
	return 0
}
