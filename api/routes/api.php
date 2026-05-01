<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\EntrepriseController;
use App\Http\Controllers\Api\UserController;
use App\Http\Controllers\Api\POSPointController;
use App\Http\Controllers\Api\CoreProductCategoryController;
use App\Http\Controllers\Api\CoreProductController;
use App\Http\Controllers\Api\ComptaClassesController;
use App\Http\Controllers\Api\ComptaComptesController;
use App\Http\Controllers\Api\ComptaJournauxController;
use App\Http\Controllers\Api\ComptaConfigController;
use App\Http\Controllers\Api\CoreFournisseurController;
use App\Http\Controllers\Api\AchatCommandeController;
use App\Http\Controllers\Api\StockWarehouseController;
use App\Http\Controllers\Api\StockMouvementController;
use App\Http\Controllers\Api\StockInventaireController;
use App\Http\Controllers\Api\StockProduitEntrepotController;
use App\Http\Controllers\Api\ShopClientController;
use App\Http\Controllers\Api\ShopPanierController;
use App\Http\Controllers\Api\ShopExpenseController;
use App\Http\Controllers\Api\RestauSalleController;
use App\Http\Controllers\Api\RestauTableController;
use App\Http\Controllers\Api\RestauPanierController;
use App\Http\Controllers\Api\RestauExpenseController;
use App\Http\Controllers\Api\HotelCategoryController;
use App\Http\Controllers\Api\HotelRoomController;
use App\Http\Controllers\Api\HotelReservationController;
use App\Http\Controllers\Api\EventClientController;
use App\Http\Controllers\Api\EventServiceController;
use App\Http\Controllers\Api\EventReservationController;
use App\Http\Controllers\Api\SyncController;

// ── Public routes ────────────────────────────────────────────────────────────
Route::post('/auth/register', [AuthController::class, 'register']);
Route::post('/auth/login',    [AuthController::class, 'login']);

// ── Protected routes (Sanctum token required) ────────────────────────────────
Route::middleware('auth:sanctum')->group(function () {

    // Auth
    Route::post('/auth/logout', [AuthController::class, 'logout']);
    Route::get('/auth/me',      [AuthController::class, 'me']);

    // Core
    Route::apiResource('entreprises',         EntrepriseController::class);
    Route::apiResource('users',               UserController::class);
    Route::apiResource('pos-points',          POSPointController::class);
    Route::apiResource('product-categories',  CoreProductCategoryController::class);
    Route::apiResource('products',            CoreProductController::class);

    // Comptabilité
    Route::apiResource('compta/classes',      ComptaClassesController::class);
    Route::apiResource('compta/comptes',      ComptaComptesController::class);
    Route::apiResource('compta/journaux',     ComptaJournauxController::class);
    Route::get('compta/config/pos/{pos_id}',  [ComptaConfigController::class, 'byPos']);
    Route::get('compta/config/{id}',          [ComptaConfigController::class, 'show']);
    Route::post('compta/config',              [ComptaConfigController::class, 'store']);
    Route::put('compta/config/{id}',          [ComptaConfigController::class, 'update']);

    // Achats
    Route::apiResource('fournisseurs',        CoreFournisseurController::class);
    Route::apiResource('achat/commandes',     AchatCommandeController::class);

    // Stock
    Route::apiResource('stock/warehouses',    StockWarehouseController::class);
    Route::apiResource('stock/mouvements',    StockMouvementController::class)->except(['update']);
    Route::apiResource('stock/inventaires',   StockInventaireController::class);
    Route::apiResource('stock/produits',      StockProduitEntrepotController::class);

    // Boutique
    Route::apiResource('shop/clients',        ShopClientController::class);
    Route::apiResource('shop/paniers',        ShopPanierController::class);
    Route::apiResource('shop/depenses',       ShopExpenseController::class);

    // Restaurant
    Route::apiResource('restau/salles',       RestauSalleController::class);
    Route::apiResource('restau/tables',       RestauTableController::class);
    Route::apiResource('restau/paniers',      RestauPanierController::class);
    Route::apiResource('restau/depenses',     RestauExpenseController::class);

    // Hôtel
    Route::apiResource('hotel/categories',    HotelCategoryController::class);
    Route::apiResource('hotel/rooms',         HotelRoomController::class);
    Route::apiResource('hotel/reservations',  HotelReservationController::class);

    // Salle de Fête
    Route::apiResource('event/clients',       EventClientController::class);
    Route::apiResource('event/services',      EventServiceController::class);
    Route::apiResource('event/reservations',  EventReservationController::class);

    // Sync
    Route::post('/sync/push',  [SyncController::class, 'push']);
    Route::get('/sync/pull',   [SyncController::class, 'pull']);
});
