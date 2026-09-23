FROM golang:1.23-alpine AS build
WORKDIR /src
COPY . .
RUN CGO_ENABLED=0 go build -o /dsu ./cmd/dsu
FROM scratch
COPY --from=build /dsu /dsu
ENTRYPOINT ["/dsu"]
