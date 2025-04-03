// Функция для форматирования содержимого FormData
const formatFormData = (formData) => {
    const formattedData = {};
    formData.forEach((value, key) => {
      // Если значение - это Blob или File, можно добавить его тип и имя файла
      if (value instanceof Blob) {
        formattedData[key] = `(Blob: ${value.type}, size: ${value.size})`;
      } else {
        formattedData[key] = value;
      }
    });
    return formattedData;
  };

  class Logger {
    constructor() {
      this.enabled = import.meta.env.VITE_LOGGING === '1';
    }

    log(message, ...args) {
      if (this.enabled) {
        console.log(message, ...this.formatArgs(args));
      }
    }

    error(message, ...args) {
      if (this.enabled) {
        console.error(message, ...this.formatArgs(args));
      }
    }

    warn(message, ...args) {
      if (this.enabled) {
        console.warn(message, ...this.formatArgs(args));
      }
    }

    info(message, ...args) {
      if (this.enabled) {
        console.info(message, ...this.formatArgs(args));
      }
    }

    formatArgs(args) {
      return args.map(arg => {
        if (arg instanceof FormData) {
          return this.formatFormData(arg);
        }
        return arg;
      });
    }

    formatFormData(formData) {
      const formattedData = {};
      formData.forEach((value, key) => {
        if (value instanceof Blob) {
          formattedData[key] = `(Blob: ${value.type}, size: ${value.size})`;
        } else {
          formattedData[key] = value;
        }
      });
      return formattedData;
    }
  }

  const logger = new Logger();
  export default logger;