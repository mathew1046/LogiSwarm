function isValidNumber(value) {
  return value != null && !isNaN(value) && isFinite(value);
}

export function formatCurrency(value) {
  if (!isValidNumber(value) || value < 0) {
    return '—';
  }
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

export function formatPercentage(value) {
  if (!isValidNumber(value) || value < 0 || value > 100) {
    return '—';
  }
  return new Intl.NumberFormat(undefined, {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  }).format(value / 100);
}

export function formatDuration(hours) {
  if (!isValidNumber(hours) || hours < 0) {
    return '—';
  }

  const days = Math.floor(hours / 24);
  const remainingHours = Math.floor(hours % 24);
  const minutes = Math.round((hours - Math.floor(hours)) * 60);

  const parts = [];

  if (days > 0) {
    parts.push(`${days}d`);
  }
  if (remainingHours > 0) {
    parts.push(`${remainingHours}h`);
  }
  if (days === 0 && minutes > 0) {
    parts.push(`${minutes}m`);
  }

  return parts.length > 0 ? parts.join(' ') : '0h';
}

export function formatWeight(kg) {
  if (!isValidNumber(kg) || kg < 0) {
    return '—';
  }
  return new Intl.NumberFormat(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(kg) + ' kg';
}

export function formatVolume(teu) {
  if (!isValidNumber(teu) || teu < 0) {
    return '—';
  }
  return new Intl.NumberFormat(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(teu) + ' TEU';
}

export function formatSpeed(knots) {
  if (!isValidNumber(knots) || knots < 0) {
    return '—';
  }
  return new Intl.NumberFormat(undefined, {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  }).format(knots) + ' kn';
}