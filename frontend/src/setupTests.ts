// jest-dom adds custom jest matchers for asserting on DOM nodes.
import '@testing-library/jest-dom';

// Mock antd's responsiveObserver to avoid window.matchMedia dependency in jsdom
jest.mock('antd/lib/_util/responsiveObserver', () => {
  const mockObserver = () => ({
    responsiveMap: {},
    matchHandlers: {},
    dispatch: jest.fn(),
    subscribe: jest.fn(() => 1),
    unsubscribe: jest.fn(),
    register: jest.fn(),
    unregister: jest.fn(),
  });
  return {
    __esModule: true,
    default: mockObserver,
    responsiveArray: ['xxl', 'xl', 'lg', 'md', 'sm', 'xs'],
    matchScreen: jest.fn(),
  };
});
