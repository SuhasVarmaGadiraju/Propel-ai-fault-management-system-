/**
 * Formatting and Utility Helper Functions
 */

export const formatNumber = (num) => {
  return new Intl.NumberFormat('en-US').format(num);
};

export const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};
