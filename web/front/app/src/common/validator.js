import { emailRegex, urlRegex } from './constants'
import { isRef } from 'vue'

const rules = {
  required: {
    rule: value => {
      const val = isRef(value) ? value.value : value
      return !!String(val).trim()
    },
    message: 'Поле обязательно для заполнения'
  },
  email: {
    rule: value => {
      const val = isRef(value) ? value.value : value
      return val ? emailRegex.test(String(val).toLowerCase()) : true
    },
    message: 'Электроная почта имеет неверный формат'
  },
  url: {
    rule: value => {
      const val = isRef(value) ? value.value : value
      return val ? urlRegex.test(val) : true
    },
    message: 'Ссылка имеет неверный формат'
  }
}

const validate = (value, appliedRules) => {
  for (const appliedRule of appliedRules) {
    if (!rules[appliedRule]) continue
    const { rule, message } = rules[appliedRule]
    if (!rule(value)) return message
  }
  return ''
}

export const validateFields = (fields, validations) => {
  let isValid = true
  Object.keys(validations).forEach(key => {
    validations[key].error = validate(fields[key], validations[key].rules)
    if (validations[key].error) {
      isValid = false
    }
  })
  return isValid
}

export const clearValidationErrors = (validations, field = null) => {
  if (!validations) return
  if (field) {
    validations[field].error = ''
  } else {
    Object.keys(validations).forEach(key => {
      validations[key].error = ''
    })
  }
}
