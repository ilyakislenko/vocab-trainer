useState | | хук состояния (React) | useState lets a component hold data that changes over time.
useEffect | | хук побочных эффектов (React) | useEffect runs code after the component renders.
useMemo | | хук мемоизации (React) | useMemo caches the result of a calculation until its dependencies change.
useCallback | | хук мемоизации функций (React) | useCallback keeps a function identity stable between renders.
useRef | | хук ссылки на DOM/значение (React) | useRef gives you a mutable value that does not trigger re-renders.
component | | компонент (React) | A component is a reusable piece of the user interface.
props | | свойства компонента | Props are read-only inputs passed into a component.
state | | состояние | State is data that a component owns and can change.
virtual DOM | | виртуальная модель DOM | The virtual DOM is an in-memory representation of the real interface.
reconciliation | | согласование изменений | Reconciliation is how React diffs old and new virtual trees.
key | | ключ списка (React) | React uses the key prop to tell list items apart.
hoc | | компонент высшего порядка | A higher-order component wraps another component to add behaviour.
render prop | | паттерн «функция-рендер» | A render prop is a function prop that controls what the component renders.
fragment | | фрагмент (React) | A fragment groups children without adding an extra node.
strict mode | | строгий режим (React) | Strict mode highlights potential problems in development.
memo | | мемоизация компонента | Wrapping a component in memo skips re-renders when props are unchanged.
lazy | | ленивая загрузка (React) | Lazy lets you load a component only when it is first needed.
suspense | | механизм ожидания (React) | Suspense shows fallback content while lazy data loads.
context | | контекст (React) | Context provides data to many components without prop drilling.
portal | | портал (React) | A portal renders a component into a different part of the DOM.
bundle | | бандл (сборка) | The bundle is the final file shipped to the browser.
tree shaking | | «встряхивание» дерева | Tree shaking removes unused code from the bundle.
hydration | | гидрация (SSR) | Hydration attaches event handlers to server-rendered markup.
side effect | | побочный эффект | A side effect is anything that happens outside the render, like an API call.
rerender | | повторный рендер | A rerender happens when state or props change.
unmount | | размонтирование | Unmounting removes a component from the screen.
event handler | | обработчик события | An event handler runs when the user interacts with the element.
controlled component | | управляемый компонент | A controlled component keeps its value in React state.
uncontrolled component | | неуправляемый компонент | An uncontrolled component manages its own DOM value.
pure function | | чистая функция | A pure function returns the same result for the same input.
immutability | | неизменяемость | Immutability means data is never changed in place.
binding | | привязка | Binding connects a method to a component instance.
closure | | замыкание | A closure remembers the variables from the scope where it was created.
async | | асинхронный | Async code does not block the rest of the program.
await | | ожидание (async/await) | Await pauses execution until a promise settles.
promise | | промис | A promise represents a value that may be available later.
callback | | функция обратного вызова | A callback is a function passed to be called later.
event loop | | цикл событий | The event loop processes microtasks and macrotasks in order.
microtask | | микрозадача | Microtasks run before the next paint and before macrotasks.
JSON | | формат обмена данными | JSON is a lightweight format for storing and exchanging data.
REST | | архитектурный стиль API | REST uses standard HTTP methods to manage resources.
API | | программный интерфейс | An API defines how different systems talk to each other.
endpoint | | конечная точка API | An endpoint is a specific URL the client can call.
request | | запрос | A request is the message the client sends to the server.
response | | ответ | A response is what the server sends back to the client.
status code | | код состояния HTTP | The status code tells the client how the request ended.
payload | | полезная нагрузка | The payload is the actual data carried by the request.
header | | заголовок HTTP | Headers carry metadata about the request or response.
middleware | | промежуточное ПО | Middleware runs between the request and the final handler.
authentication | | аутентификация | Authentication verifies who the user is.
authorization | | авторизация | Authorization decides what the user is allowed to do.
token | | токен | A token proves that the request is authorized.
session | | сессия | A session keeps state across several requests from the same user.
database | | база данных | A database stores the application's data persistently.
query | | запрос к БД | A query asks the database for specific data.
schema | | схема (БД) | The schema defines the structure of the database tables.
index | | индекс (БД) | An index speeds up lookups on a column.
transaction | | транзакция | A transaction groups operations that must all succeed together.
migration | | миграция (БД) | A migration changes the database schema in a controlled way.
SQL | | язык запросов | SQL is the standard language for relational databases.
ORM | | объектно-реляционное отображение | An ORM maps database rows to objects in code.
join | | соединение таблиц | A join combines rows from two or more tables.
foreign key | | внешний ключ | A foreign key links one table to the primary key of another.
primary key | | первичный ключ | A primary key uniquely identifies each row of a table.
cache | | кэш | A cache stores copies of data to serve requests faster.
deployment | | развёртывание | Deployment ships the new version to the running server.
server | | сервер | The server responds to requests from clients over the network.
client | | клиент | The client is the program that makes requests to the server.
frontend | | фронтенд | The frontend is everything the user sees in the browser.
backend | | бэкенд | The backend runs on the server and processes the business logic.
TypeScript | | надмножество JavaScript с типами | TypeScript adds static types on top of JavaScript.
interface | | интерфейс (TS) | An interface describes the shape of an object.
type | | тип (TS) | A type describes the shape that a value must have.
enum | | перечисление (TS) | An enum defines a set of named constants.
generic | | дженерик (TS) | A generic lets a function work with any type.
union type | | объединение типов | A union type means a value can be one of several types.
optional | | необязательный | An optional field may or may not be present.
nullable | | допускающий null | A nullable value can be null as well as its own type.
inference | | вывод типов | Inference means TypeScript figures out a type by itself.
annotation | | аннотация типа | An annotation is the type written explicitly on a variable.
const | | константа | Const declares a value that cannot be reassigned.
let | | изменяемая переменная | Let declares a variable whose value can change.
arrow function | | стрелочная функция | An arrow function is a short way to write a function.
spread | | оператор распространения | Spread copies elements of an array or object.
destructuring | | деструктуризация | Destructuring unpacks values from arrays or objects.
type safety | | безопасность типов | Type safety prevents errors by checking types at compile time.
compiler | | компилятор | The compiler turns TypeScript into plain JavaScript.
module | | модуль | A module is a file that exports and imports code.
import | | импорт | Import brings exported code from another module.
export | | экспорт | Export makes code available to other modules.
